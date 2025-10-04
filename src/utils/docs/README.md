# PrinterReaper - Online Discovery Module

## Overview

This module enables automated discovery of PJL-compatible printers exposed on the internet using **Shodan** and **Censys** APIs. It searches for the 2,586 printer models listed in `src/core/db/pjl.dat` and generates comprehensive reports.

## Features

- ✅ **Dual API Support**: Shodan as primary, Censys as fallback
- ✅ **Smart Query Generation**: Optimized searches based on printer database
- ✅ **2,586 Printer Models**: Covers HP, Brother, Xerox, Ricoh, Kyocera, Lexmark, Sharp, Dell, and more
- ✅ **Duplicate Removal**: Intelligent deduplication by IP address
- ✅ **Multi-Format Export**: JSON, CSV, and HTML reports
- ✅ **Rate Limiting**: Configurable delays to respect API limits
- ✅ **Comprehensive Statistics**: Country distribution, organization analysis, and more

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements_discovery.txt
```

Or manually:

```bash
pip install shodan censys requests
```

### 2. Get API Keys

#### Shodan (Recommended)
1. Sign up at https://account.shodan.io/register
2. Get your API key from https://account.shodan.io/
3. Free tier includes 100 query credits/month

#### Censys (Fallback)
1. Sign up at https://censys.io/register
2. Get API credentials from https://censys.io/account/api
3. Free tier includes 250 queries/month

### 3. Configure API Keys

#### Linux/macOS:
```bash
export SHODAN_API_KEY="your_shodan_api_key_here"
export CENSYS_API_ID="your_censys_id_here"
export CENSYS_API_SECRET="your_censys_secret_here"
```

#### Windows (PowerShell):
```powershell
$env:SHODAN_API_KEY="your_shodan_api_key_here"
$env:CENSYS_API_ID="your_censys_id_here"
$env:CENSYS_API_SECRET="your_censys_secret_here"
```

#### Windows (CMD):
```cmd
set SHODAN_API_KEY=your_shodan_api_key_here
set CENSYS_API_ID=your_censys_id_here
set CENSYS_API_SECRET=your_censys_secret_here
```

## Usage

### Quick Test

Run the test suite to verify everything is working:

```bash
# Test database loading only (no API required)
python test_discovery_online.py

# Test with Shodan API
export SHODAN_API_KEY="your_key"
python test_discovery_online.py

# Run full discovery test (limited to 5 queries, 10 results each)
python test_discovery_online.py --full-test --max-queries 5 --max-results 10
```

### Programmatic Usage

```python
from src.utils.discovery_online import OnlineDiscoveryManager

# Initialize manager
manager = OnlineDiscoveryManager()

# Run discovery
summary = manager.discover(
    max_results_per_query=100,  # Results per query
    delay_between_queries=1.5,   # Delay in seconds
    use_shodan=True,             # Use Shodan API
    use_censys=True              # Use Censys as fallback
)

# Print summary
print(f"Total devices found: {summary['total_devices']}")
print(f"Countries: {len(summary['countries'])}")

# Export results
manager.export_results(output_dir="discovery_results")
```

### Advanced Usage

```python
from src.utils.discovery_online import (
    PrinterDatabase,
    ShodanDiscovery,
    CensysDiscovery
)

# Load printer database
db = PrinterDatabase("src/core/db/pjl.dat")
print(f"Loaded {len(db.models)} printer models")
print(f"Brands: {list(db.brands.keys())}")

# Get optimized queries
queries = db.get_search_queries(limit_per_brand=3)
print(f"Generated {len(queries)} queries")

# Use Shodan directly
shodan = ShodanDiscovery(api_key="your_key")
results = shodan.search('port:9100 "HP LaserJet"', max_results=50)

for result in results:
    print(f"{result['ip']} - {result['country']} - {result['org']}")

# Use Censys directly
censys = CensysDiscovery(api_id="your_id", api_secret="your_secret")
results = censys.search('services.port: 9100', max_results=50)
```

## Query Examples

### Shodan Queries

```python
# Generic PJL search
"port:9100 PJL"

# Specific manufacturer
"HP LaserJet" port:9100
"Brother HL-" port:9100
"Xerox Phaser" port:9100

# Specific model
"HP LaserJet 4050" port:9100
"Brother HL-5370DW" port:9100

# PJL Ready message
"PJL Ready" port:9100
```

### Censys Queries

```python
# Port search
services.port: 9100

# Banner search
services.banner: "PJL Ready" and services.port: 9100

# Service name
services.service_name: "jetdirect"
```

## Output Formats

### JSON
```json
{
  "summary": {
    "total_devices": 1234,
    "total_queries": 35,
    "countries": {
      "United States": 456,
      "Germany": 123,
      "United Kingdom": 89
    },
    "sources": {
      "shodan": 1100,
      "censys": 134
    }
  },
  "results": [
    {
      "ip": "1.2.3.4",
      "port": 9100,
      "country": "United States",
      "org": "Example Corp",
      "product": "HP LaserJet",
      "banner": "...",
      "source": "shodan"
    }
  ]
}
```

### CSV
Comma-separated values with columns:
- ip
- port
- hostnames
- org
- country
- country_code
- city
- banner
- timestamp
- product
- version
- source
- query_type
- query_description

### HTML
Interactive HTML report with:
- Summary statistics
- Country distribution table
- Top organizations
- Device listing with clickable links

## Test Suite

### Available Tests

1. **Database Test**: Loads and validates printer database
2. **Shodan Test**: Tests Shodan API connection and search
3. **Censys Test**: Tests Censys API connection and search
4. **Full Discovery**: Runs complete discovery workflow

### Test Options

```bash
# Run all tests
python test_discovery_online.py --full-test

# Skip specific tests
python test_discovery_online.py --skip-shodan
python test_discovery_online.py --skip-censys

# Limit full test scope
python test_discovery_online.py --full-test --max-queries 3 --max-results 5

# Help
python test_discovery_online.py --help
```

### Expected Output

```
==================================================================
  PrinterReaper - Online Discovery Module Test Suite
==================================================================
  Date: 2025-10-04 12:00:00
==================================================================

[*] API Key Status:
    SHODAN_API_KEY: ✓ Set
    CENSYS_API_ID: ✓ Set
    CENSYS_API_SECRET: ✓ Set

==================================================================
TEST 1: Printer Database
==================================================================
[✓] Loaded 2586 printer models
[✓] Identified 15 brands

[*] Brand Distribution:
    HP                  :  600 models
    Brother             :  300 models
    Xerox               :  200 models
    ...

==================================================================
  TEST SUMMARY
==================================================================
  [✓] DATABASE       : PASSED
  [✓] SHODAN         : PASSED
  [✓] CENSYS         : PASSED
  [✓] DISCOVERY      : PASSED
==================================================================

[✓] All tests passed!
```

## Architecture

### Class Hierarchy

```
OnlineDiscoveryManager
├── PrinterDatabase
│   ├── load_database()
│   ├── categorize_by_brand()
│   └── get_search_queries()
├── ShodanDiscovery
│   ├── search()
│   └── get_api_info()
└── CensysDiscovery
    ├── search()
    ├── convert_query()
    └── get_api_info()
```

### Workflow

1. **Load Database**: Read printer models from `pjl.dat`
2. **Categorize**: Group models by brand
3. **Generate Queries**: Create optimized search queries
4. **Search Shodan**: Execute queries on Shodan
5. **Fallback to Censys**: If Shodan fails or finds nothing
6. **Deduplicate**: Remove duplicate IPs
7. **Generate Reports**: Export to JSON, CSV, HTML

## Performance

### API Limits

| API | Free Tier | Paid Tier |
|-----|-----------|-----------|
| Shodan | 100 queries/month | Unlimited |
| Censys | 250 queries/month | Higher limits |

### Optimization Tips

1. **Reduce queries**: Use `limit_per_brand` parameter
2. **Increase delay**: Set `delay_between_queries` higher
3. **Limit results**: Reduce `max_results_per_query`
4. **Cache results**: Export and reuse data

### Estimated Times

- Database loading: < 1 second
- Single Shodan query: 1-3 seconds
- Single Censys query: 2-5 seconds
- Full discovery (35 queries): ~2-5 minutes

## Security Considerations

### ⚠️ Legal Notice

This tool is for **authorized security research and testing only**. Unauthorized access to computer systems is illegal under laws like:
- USA: Computer Fraud and Abuse Act (CFAA)
- EU: General Data Protection Regulation (GDPR)
- Brazil: Lei Geral de Proteção de Dados (LGPD)

### Best Practices

1. ✅ **Get Permission**: Only test systems you own or have authorization to test
2. ✅ **Responsible Disclosure**: Report vulnerabilities responsibly
3. ✅ **Rate Limiting**: Respect API terms of service
4. ✅ **Data Privacy**: Handle discovered data responsibly
5. ✅ **Ethical Use**: Use for defense, not offense

### What This Tool Does

- ✅ Searches public databases (Shodan/Censys)
- ✅ Finds publicly exposed devices
- ✅ Generates reports for security assessment

### What This Tool Does NOT Do

- ❌ Does not exploit vulnerabilities
- ❌ Does not access devices without permission
- ❌ Does not modify or damage systems

## Troubleshooting

### API Key Errors

```
[!] Shodan API key not provided
```

**Solution**: Set `SHODAN_API_KEY` environment variable

### Import Errors

```
[!] Shodan module not installed
```

**Solution**: Run `pip install shodan censys`

### No Results Found

This is normal if:
- Query is too specific
- No devices match the criteria
- Free tier limitations

### Rate Limiting

```
[!] Shodan API Error: Rate limit exceeded
```

**Solution**: 
- Increase `delay_between_queries`
- Reduce number of queries
- Wait for quota reset

### Censys Fallback Not Working

Ensure both `CENSYS_API_ID` and `CENSYS_API_SECRET` are set.

## Printer Database

The module uses `src/core/db/pjl.dat` containing 2,586 printer models:

### Top Brands
- **HP**: ~600 models (LaserJet, Color LaserJet, DesignJet, etc.)
- **Brother**: ~300 models (HL, MFC, DCP series)
- **Xerox**: ~200 models (Phaser, WorkCentre)
- **Ricoh**: ~150 models (Aficio series)
- **Kyocera**: ~200 models (FS, KM, TASKalfa)
- **Lexmark**: ~150 models (Optra, MS, MX, CS, CX)
- **Sharp**: ~100 models (AR, MX series)
- And 8+ more brands...

### Common Models Found
- HP LaserJet 4000/4050/4100/4200/4250
- HP LaserJet P2015/P3005/P4015
- Brother HL-5370DW/5450DN/5470DW
- Xerox Phaser 6500DN/8560DN
- Ricoh Aficio MP 2500/3500/4500

## Future Enhancements

- [ ] Integration with PrinterReaper main CLI
- [ ] Real-time monitoring mode
- [ ] Automatic vulnerability assessment
- [ ] Email notifications
- [ ] API rate limit auto-adjustment
- [ ] Machine learning for model detection
- [ ] Geolocation mapping visualization
- [ ] Scheduled scans with cron integration

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Test your changes with `test_discovery_online.py`
2. Update documentation if adding features
3. Follow PEP 8 style guidelines
4. Add type hints where applicable

## License

MIT License - See LICENSE file for details

## Authors

PrinterReaper Team

## Support

For issues, questions, or contributions:
- GitHub Issues: [your-repo]/issues
- Email: [your-email]

---

**Remember**: Always use this tool ethically and legally! 🔒

