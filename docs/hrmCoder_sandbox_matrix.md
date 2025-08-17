# Sandbox Feature Parity

The table below compares capabilities across the supported sandbox adapters.

| Capability                | isolate | nsjail | gVisor (runsc) |
|--------------------------|:-------:|:------:|:--------------:|
| CPU time limit           | ✅       | ✅     | ❌ *not implemented* |
| Wall clock limit         | ✅       | ✅     | ❌ *not implemented* |
| Memory limit             | ✅       | ✅     | ✅ |
| Process count limit      | ✅       | ✅     | ✅ |
| Network isolation        | ✅       | ✅     | ✅ |
| Read-only mounts         | ✅       | ✅     | ✅ |
| Working directory mount  | ✅       | ✅     | ✅ |
| Environment variables    | ✅       | ✅     | ✅ |
| Stdout/stderr capture    | ✅       | ✅     | ✅ |
| Output size trimming     | ✅       | ✅     | ✅ |
| File size limit          | ✅       | ✅     | ❌ *pending* |

*`gVisor` support mirrors Docker's `runsc` runtime. CPU and wall time limits are
not currently exposed and file size limits require further investigation.*
