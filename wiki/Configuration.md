# Configuration

PrinterReaper reads a `config.json` file for API keys and runtime settings.

---

## Check Current Configuration

```bash
python printer-reaper.py --check-config
```

**Output:**
```
  API Configuration Check
  ─────────────────────────────────────────────────────────
  Shodan    : CONFIGURED   (online discovery enabled)
  Censys    : NOT SET      (--discover-online limited to Shodan)
  NVD       : CONFIGURED   (enhanced CVE lookup active)
  ML Engine : ENABLED      (scikit-learn installed)
```

---

## Config File Location

By default, PrinterReaper looks for `config.json` in the project root (same directory as `printer-reaper.py`).

Use a custom path with:
```bash
python printer-reaper.py --config /path/to/my_config.json [...]
```

---

## Full config.json Structure

```json
{
  "shodan": {
    "api_key": "YOUR_SHODAN_API_KEY"
  },
  "censys": {
    "api_id":     "YOUR_CENSYS_API_ID",
    "api_secret": "YOUR_CENSYS_API_SECRET"
  },
  "nvd": {
    "api_key": "YOUR_NVD_API_KEY"
  },
  "ml": {
    "enabled": true
  },
  "network": {
    "timeout":      6,
    "snmp_timeout": 3,
    "http_timeout": 8,
    "raw_timeout":  5,
    "threads":      60
  },
  "bruteforce": {
    "default_delay": 0.3,
    "max_workers":   4
  }
}
```

---

## Field Reference

### shodan

| Field | Description |
|-------|-------------|
| `api_key` | Shodan API key from [shodan.io](https://account.shodan.io) |

Required for: `--discover-online`, `--osint`

---

### censys

| Field | Description |
|-------|-------------|
| `api_id` | Censys API ID from [censys.io](https://search.censys.io/account/api) |
| `api_secret` | Censys API secret |

Required for: `--discover-online` (supplementary to Shodan)

---

### nvd

| Field | Description |
|-------|-------------|
| `api_key` | NVD API key from [nvd.nist.gov](https://nvd.nist.gov/developers/request-an-api-key) |

Required for: `--scan` CVE lookup (higher rate limit). Without it, the tool falls back to the built-in CVE database and unauthenticated NVD API (limited to 5 req/30s).

---

### ml

| Field | Default | Description |
|-------|---------|-------------|
| `enabled` | `true` | Enable ML-assisted fingerprinting and attack scoring |

Requires `scikit-learn` installed. Set to `false` to disable ML globally.

---

### network

| Field | Default | Description |
|-------|---------|-------------|
| `timeout` | `6` | Default socket connection timeout (seconds) |
| `snmp_timeout` | `3` | SNMP-specific timeout |
| `http_timeout` | `8` | HTTP request timeout |
| `raw_timeout` | `5` | RAW/9100 socket timeout |
| `threads` | `60` | Thread count for local discovery subnet scan |

---

### bruteforce

| Field | Default | Description |
|-------|---------|-------------|
| `default_delay` | `0.3` | Default delay between login attempts (can be overridden with `--bf-delay`) |
| `max_workers` | `4` | Maximum parallel brute-force threads |

---

## Getting API Keys

### Shodan
1. Register at [shodan.io](https://shodan.io)
2. Go to [Account > API Key](https://account.shodan.io)
3. Copy the key into `config.json`

### Censys
1. Register at [censys.io](https://censys.io)
2. Go to [Account > API](https://search.censys.io/account/api)
3. Copy API ID and secret into `config.json`

### NVD (National Vulnerability Database)
1. Request at [nvd.nist.gov/developers/request-an-api-key](https://nvd.nist.gov/developers/request-an-api-key)
2. Key is emailed within minutes
3. Copy into `config.json`

---

## Example Setup

```bash
cp config.json.example config.json

# Edit config.json and add your keys
# Then verify:
python printer-reaper.py --check-config
```

---

## Running Without API Keys

All core features work without any API keys:

| Feature | Without keys | With keys |
|---------|-------------|-----------|
| `--discover-local` | Full functionality | Same |
| `--scan` | Built-in CVE DB only | NVD API (more CVEs, faster) |
| `--scan-ml` | ML disabled if no scikit-learn | ML enabled |
| `--discover-online` | Not available | Full Shodan + Censys search |
| `--osint` | Not available | Target IP lookup |
| `--bruteforce` | Full functionality | Same |
| `--xpl-*` | Full functionality | Same |
| `--attack-matrix` | Full functionality | Same |
