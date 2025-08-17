# Sandbox Binary Adapter

`BinarySandboxAdapter` runs compiled executables inside a sandbox backend
while applying deterministic sanitizer settings.  It works with
`IsolateRunner`, `NSJailRunner`, and `GVisorRunner` and forwards resource
limits such as CPU time, memory, and stdout/stderr caps.

## Usage

```python
from runners import IsolateRunner, BinarySandboxAdapter

runner = IsolateRunner()
adapter = BinarySandboxAdapter(runner)

code, out, err = adapter.run(binary_path, timeout=2.0,
                             memory_limit=256 * 1024 * 1024)
```

The adapter mounts the binary's directory read-only and executes the
process in a temporary working directory with networking disabled and a
single-process limit.

## Sanitizer environment

By default the adapter injects stable settings for AddressSanitizer and
UndefinedBehaviorSanitizer:

- `ASAN_OPTIONS=detect_leaks=0:halt_on_error=1:color=never`
- `UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1:color=never`

Custom mappings may be passed through the ``sanitizer_env`` constructor
argument.  ``run(..., sanitize_env=False)`` disables injection or allows
overrides via the ``env`` parameter.

`runners.cpp_runner.run_binary` automatically creates a
`BinarySandboxAdapter` when a sandbox runner is provided.

