# service-health-check

One small health-check runner for the three things most services need to prove:
a systemd unit is active, a TCP port accepts connections, and an HTTP endpoint
answers with the expected status.

## Features

- JSON configuration with three check types: `systemd`, `tcp`, `http`.
- Table output plus exit code `0`/`1`, and `--json` for monitoring pipelines.
- Timeouts per check; no retries by default so failures are visible immediately.
- Tests start local TCP/HTTP servers; the systemd check is skipped where
  `systemctl` is unavailable.

## Installation

```bash
git clone https://github.com/victor-harden/service-health-check.git
cd service-health-check
```

## Usage

```bash
python3 health_check.py checks.example.json
python3 health_check.py checks.example.json --json
```

Example configuration:

```json
{
  "checks": [
    {"name": "nginx", "type": "systemd", "unit": "nginx.service"},
    {"name": "postgres", "type": "tcp", "host": "127.0.0.1", "port": 5432},
    {"name": "api", "type": "http", "url": "https://example.com/health", "expect": 200}
  ]
}
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT — see [LICENSE](LICENSE).
