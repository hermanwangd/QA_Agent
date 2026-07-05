# pi-run v0.2.3 Docker Cleanup Check

Date: 2026-07-05 Asia/Taipei

Command:

```bash
/usr/local/bin/docker ps -a --filter "name=<run_id>" --format "{{.Names}}"
```

Result:

| Run ID | Leftover Containers |
|---|---:|
| `PIRUN-V023-NATS-2` | 0 |
| `PIRUN-V023-WIREMOCK-3` | 0 |
| `PIRUN-V023-JDBC-2` | 0 |
| `PIRUN-V023-FULL-4` | 0 |

Assessment: PASS.
