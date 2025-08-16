"""Environment pinning utilities for deterministic behavior."""
from __future__ import annotations

import locale
import os
import random
import time
from typing import Optional


def pin_environment(seed: int = 0, timezone: str = "UTC", locale_name: str = "C") -> None:
    """Pin PRNG seeds and normalize process-wide environment.

    Parameters
    ----------
    seed:
        Seed used for Python's ``random`` and, if available, NumPy and PyTorch.
    timezone:
        Timezone used for the process. Defaults to ``UTC``.
    locale_name:
        Locale identifier passed to :func:`locale.setlocale`.
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)

    # Optional libraries
    try:
        import numpy as np  # type: ignore

        np.random.seed(seed)
    except Exception:
        pass

    try:
        import torch  # type: ignore

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        try:
            torch.use_deterministic_algorithms(True)
        except Exception:
            pass
    except Exception:
        pass

    os.environ["TZ"] = timezone
    try:
        time.tzset()
    except AttributeError:
        pass

    try:
        locale.setlocale(locale.LC_ALL, locale_name)
    except locale.Error:
        pass
