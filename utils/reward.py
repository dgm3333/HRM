from dataclasses import dataclass, field
from typing import Dict, List
import logging

from .diagnostics import (
    clang_tidy_score,
    cppcheck_score,
    coverage_delta,
    sanitizer_clean,
)


@dataclass
class RewardAggregator:
    """Aggregates multiple reward signals into a single scalar.

    Parameters
    ----------
    weights: mapping of signal name to weight. Supported keys are
        ``compile``, ``tests``, ``coverage``, ``coverage_delta``,
        ``lint``, ``static`` and ``sanitizer``.
    max_edit_penalty: maximum penalty applied for edit cost.
    max_time_penalty: maximum penalty applied when runtime exceeds the limit.
    max_memory_penalty: maximum penalty applied when memory use exceeds the limit.
    """

    weights: Dict[str, float]
    max_edit_penalty: float = 0.1
    max_time_penalty: float = 0.1
    max_memory_penalty: float = 0.1
    history: List[float] = field(default_factory=list)

    def compute(
        self,
        compile_success: bool,
        tests_passed: int,
        tests_total: int,
        coverage: float,
        edit_cost: float,
        time_used: float,
        memory_used: float,
        lint_score: float = 1.0,
        static_score: float = 1.0,
        sanitizer_clean: bool | None = None,
        prev_coverage: float | None = None,
        time_limit: float | None = None,
        memory_limit: float | None = None,
    ) -> float:
        """Compute aggregate reward with penalties.

        Parameters
        ----------
        compile_success: whether compilation (and link) succeeded.
        tests_passed: number of unit tests passed.
        tests_total: total number of unit tests executed.
        coverage: code coverage ratio in [0, 1].
        edit_cost: number of edit operations performed.
        time_used: wall-clock seconds consumed.
        memory_used: peak memory usage in megabytes.
        lint_score: normalized score from clang-tidy/clang diagnostics.
        static_score: normalized score from static analysis tools (e.g. cppcheck).
        sanitizer_clean: whether Address/UndefinedBehavior sanitizers reported
            no issues. ``None`` skips this signal.
        prev_coverage: previous coverage value used to compute coverage delta.
        time_limit: optional runtime limit.
        memory_limit: optional memory limit.
        """

        reward = 0.0

        compile_score = 1.0 if compile_success else 0.0
        test_score = tests_passed / tests_total if tests_total else 0.0
        coverage_score = max(0.0, min(coverage, 1.0))
        prev_cov = (
            max(0.0, min(prev_coverage, 1.0))
            if prev_coverage is not None
            else None
        )
        cov_delta = coverage_delta(prev_cov, coverage_score) if prev_cov is not None else 0.0

        reward += self.weights.get("compile", 0.0) * compile_score
        reward += self.weights.get("tests", 0.0) * test_score
        reward += self.weights.get("coverage", 0.0) * coverage_score
        reward += self.weights.get("coverage_delta", 0.0) * cov_delta
        reward += self.weights.get("lint", 0.0) * max(0.0, min(lint_score, 1.0))
        reward += self.weights.get("static", 0.0) * max(0.0, min(static_score, 1.0))
        if sanitizer_clean is not None:
            san_score = 1.0 if sanitizer_clean else -1.0
            reward += self.weights.get("sanitizer", 0.0) * san_score

        # Penalties
        reward -= min(edit_cost * self.max_edit_penalty, self.max_edit_penalty)

        if time_limit and time_used > time_limit:
            over = (time_used - time_limit) / time_limit
            reward -= min(over * self.max_time_penalty, self.max_time_penalty)

        if memory_limit and memory_used > memory_limit:
            over = (memory_used - memory_limit) / memory_limit
            reward -= min(over * self.max_memory_penalty, self.max_memory_penalty)

        # Record history for histogram logging
        self.history.append(reward)
        return reward

    def compute_from_outputs(
        self,
        compile_success: bool,
        tests_passed: int,
        tests_total: int,
        coverage: float,
        edit_cost: float,
        time_used: float,
        memory_used: float,
        clang_output: str = "",
        cppcheck_output: str = "",
        sanitizer_output: str | None = None,
        prev_coverage: float | None = None,
        time_limit: float | None = None,
        memory_limit: float | None = None,
    ) -> float:
        """Compute reward using raw diagnostics output strings.

        Convenience wrapper that parses ``clang_output``, ``cppcheck_output``
        and ``sanitizer_output`` into normalized scores before delegating to
        :meth:`compute`.

        Parameters
        ----------
        clang_output:
            Raw stderr/stdout from clang-tidy/clang++.
        cppcheck_output:
            Raw output from cppcheck.
        sanitizer_output:
            Combined stdout/stderr from sanitizer-instrumented runs. ``None``
            skips sanitizer scoring.
        prev_coverage:
            Previous coverage used to compute deltas.
        time_limit:
            Optional runtime limit used for penalties.
        memory_limit:
            Optional memory limit used for penalties.
        """

        lint = clang_tidy_score(clang_output)
        static = cppcheck_score(cppcheck_output)
        san = (
            sanitizer_clean(sanitizer_output)
            if sanitizer_output is not None
            else None
        )
        return self.compute(
            compile_success=compile_success,
            tests_passed=tests_passed,
            tests_total=tests_total,
            coverage=coverage,
            edit_cost=edit_cost,
            time_used=time_used,
            memory_used=memory_used,
            lint_score=lint,
            static_score=static,
            sanitizer_clean=san,
            prev_coverage=prev_coverage,
            time_limit=time_limit,
            memory_limit=memory_limit,
        )

    def histogram(self, bins: int = 10) -> List[int]:
        """Return a simple histogram of historical rewards."""

        if not self.history:
            return [0] * bins

        mn, mx = min(self.history), max(self.history)
        step = (mx - mn) / bins if mx > mn else 1.0
        hist = [0] * bins
        for value in self.history:
            idx = int((value - mn) / step) if step else 0
            idx = min(idx, bins - 1)
            hist[idx] += 1
        return hist

    def log_histogram(self, logger: logging.Logger | None = None) -> None:
        """Log histogram of rewards with a sanity range check."""

        logger = logger or logging.getLogger(__name__)
        hist = self.histogram()
        if any(r < -1.0 or r > 1.0 for r in self.history):
            logger.warning("reward out of expected [-1,1] range")
        logger.debug("reward histogram: %s", hist)
