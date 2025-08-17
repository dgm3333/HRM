# Binary Sandbox Adapter

The `BinarySandboxAdapter` executes compiled binaries inside one of the sandbox
runners (e.g. `IsolateRunner`, `NSJailRunner`, or `GVisorRunner`). It injects
AddressSanitizer (ASan) and UndefinedBehaviorSanitizer (UBSan) environment
settings so that sanitized builds behave deterministically across different
backends.

## Usage

```python
from pathlib import Path
from runners import NSJailRunner, BinarySandboxAdapter

runner = NSJailRunner()
adapter = BinarySandboxAdapter(runner)
code, out, err = adapter.run(Path("./a.out"))
```

The adapter forwards resource limits such as `timeout` and `memory_limit` to the
underlying runner and disables network access by default.

## Sanitizer configuration

By default the adapter injects the following environment variables:

- `ASAN_OPTIONS=detect_leaks=0:halt_on_error=1:color=never`
- `UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1:color=never`

These values make sanitizer output consistent and terminate execution on the
first detected issue. Additional variables may be provided via the `env`
argument, or the defaults can be replaced entirely by passing
`BinarySandboxAdapter(..., sanitizer_env={...})`.

Set `sanitize_env=False` when calling `run` to skip the injection altogether.
