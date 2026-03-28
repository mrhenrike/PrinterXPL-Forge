# Online Discovery — Dork Mode (v3.9.0)

`--discover-online` uses a structured dork system across **5 search engines**: Shodan, Censys, FOFA, ZoomEye, Netlas.

**Rules:**
- Printer context is always implicit — never specify "printer" in filters
- At least one `--dork-*` filter is required — unfiltered global sweeps are blocked
- Each engine uses its own native query syntax (generated automatically)
- API credentials are loaded from `config.json`; engines without credentials are skipped

---

## Quick Examples

```bash
# All Epson + Ricoh printers in Latin America with port 515 — all configured engines
python printer-reaper.py --discover-online \
  --dork-vendor epson --dork-vendor ricoh \
  --dork-region latin_america \
  --dork-port 515

# HP DeskJet Pro 5500 in Brazil — Shodan + FOFA
python printer-reaper.py --discover-online \
  --dork-vendor hp \
  --dork-model "deskjet pro 5500" \
  --dork-country brazil \
  --dork-engine shodan,fofa

# All printers in São Paulo with port 9100 — all engines
python printer-reaper.py --discover-online \
  --dork-country BR \
  --dork-city "Sao Paulo" \
  --dork-port 9100

# Kyocera printers in Europe, export up to 200 results — Netlas only
python printer-reaper.py --discover-online \
  --dork-vendor kyocera \
  --dork-engine netlas \
  --dork-region europe \
  --dork-limit 200

# Ricoh printers in specific organization (ISP or company)
python printer-reaper.py --discover-online \
  --dork-vendor ricoh \
  --dork-org "Petrobras"

# Brother printers by CPE on Censys (model-specific)
python printer-reaper.py --discover-online \
  --dork-cpe "cpe:/h:brother:mfc-l8900cdw"

# Multiple countries, multiple vendors, multiple ports
python printer-reaper.py --discover-online \
  --dork-vendor hp --dork-vendor canon \
  --dork-country BR --dork-country AR --dork-country CO \
  --dork-port 9100 --dork-port 631 \
  --dork-limit 50
```

---

## All Dork Flags

| Flag | Repeatable | Description |
|------|-----------|-------------|
| `--dork-vendor VENDOR` | Yes | Vendor name (see supported list below) |
| `--dork-model MODEL` | No | Model string to search in banner |
| `--dork-country COUNTRY` | Yes | ISO-3166 code or full name (pt-BR/en) |
| `--dork-city CITY` | No | City name |
| `--dork-region REGION` | Yes | Geographic region (see list below) |
| `--dork-port PORT` | Yes | Port number (9100, 515, 631, 80, 443) |
| `--dork-org ORG` | No | Organization / ISP name |
| `--dork-cpe CPE` | No | CPE identifier (Censys/Netlas) |
| `--dork-limit N` | No | Max results per query (default: 100) |
| `--dork-engine ENGINE[,ENGINE]` | No | Engines to use: `shodan`, `censys`, `fofa`, `zoomeye`, `netlas`. Default: all with valid credentials. |

### Requirement

At least one `--dork-*` filter must be provided. If none are given and no target IP is specified, the program exits with an explanatory error message.

---

## Search Engines

### Available Engines

| Engine | Flag value | API Docs | Free tier |
|--------|-----------|---------|-----------|
| Shodan | `shodan` | https://account.shodan.io/ | 1 credit/query |
| Censys | `censys` | https://search.censys.io/account/api | 250 queries/month |
| FOFA | `fofa` | https://en.fofa.info/api | Limited (account required) |
| ZoomEye | `zoomeye` | https://www.zoomeye.org/profile | 10,000 results/month |
| Netlas | `netlas` | https://app.netlas.io/profile/ | 50 queries/day |

### Engine Selection

```bash
# Use all configured engines (default)
python printer-reaper.py --discover-online --dork-vendor hp --dork-country BR

# Use specific engines only
python printer-reaper.py --discover-online --dork-vendor hp --dork-country BR \
  --dork-engine shodan,fofa,netlas

# Single engine
python printer-reaper.py --discover-online --dork-vendor epson --dork-port 9100 \
  --dork-engine zoomeye
```

### Query Syntax Per Engine

The same `DiscoveryParams` is automatically translated to each engine's native syntax:

| Engine | Example query |
|--------|--------------|
| Shodan | `"HP LaserJet" country:BR port:9100` |
| Censys | `services.banner="HP LaserJet" AND location.country_code="BR" AND services.port=9100` |
| FOFA | `banner="HP LaserJet" && country="BR" && port="9100"` |
| ZoomEye | `banner:"HP LaserJet" +country:"BR" +port:9100` |
| Netlas | `data.response:"HP LaserJet" AND geo.country_code:"BR" AND port:9100` |

### Credentials Configuration

Add to `config.json`:

```json
{
  "shodan":  [{ "label": "primary", "api_key": "YOUR_SHODAN_KEY" }],
  "censys":  [{ "label": "primary", "api_id": "...", "api_secret": "..." }],
  "fofa":    [{ "label": "primary", "email": "you@example.com", "api_key": "YOUR_FOFA_KEY" }],
  "zoomeye": [{ "label": "primary", "api_key": "YOUR_ZOOMEYE_KEY" }],
  "netlas":  [{ "label": "primary", "api_key": "YOUR_NETLAS_KEY" }]
}
```

Engines without valid credentials are silently skipped. Run `python printer-reaper.py --check-config` to see which engines are active.

---

## Supported Vendors

| `--dork-vendor` value | Searches for |
|----------------------|--------------|
| `hp` | HP LaserJet, OfficeJet, DeskJet, Color LaserJet, Hewlett-Packard |
| `epson` | EPSON, Epson |
| `ricoh` | Ricoh, Aficio |
| `xerox` | Xerox, Phaser, WorkCentre |
| `brother` | Brother |
| `canon` | Canon, imageRUNNER |
| `kyocera` | Kyocera, TASKalfa, FS- |
| `konica` | Konica Minolta, bizhub |
| `samsung` | Samsung |
| `lexmark` | Lexmark |
| `sharp` | Sharp, MX- |
| `oki` | OKI, OKIDATA |
| `toshiba` | Toshiba, e-Studio |
| `fujifilm` | Fujifilm, Fuji Xerox |
| `zebra` | Zebra |
| `pantum` | Pantum |
| `sindoh` | Sindoh |
| `develop` | Develop, ineo |
| `utax` | UTAX, Triumph-Adler |
| `dell` | Dell |

---

## Supported Regions

| `--dork-region` value | Countries |
|----------------------|-----------|
| `latin_america` | AR, BO, BR, CL, CO, CR, CU, DO, EC, GT, HN, MX, NI, PA, PE, PR, SV, UY, VE |
| `south_america` | AR, BO, BR, CL, CO, EC, GY, PE, PY, SR, UY, VE |
| `central_america` | CR, GT, HN, MX, NI, PA, SV, BZ |
| `north_america` | US, CA, MX |
| `europe` | GB, DE, FR, IT, ES, PT, NL, BE, CH, AT, SE, NO, DK, FI, PL, CZ, HU, RO, BG, HR, GR, IE, SK, SI, EE, LT, LV |
| `eastern_europe` | PL, CZ, HU, RO, BG, SK, UA, BY, MD, RS, BA, AL, MK |
| `asia` | CN, JP, KR, IN, SG, MY, TH, VN, ID, PH, TW, HK, BD, PK, LK, MM |
| `southeast_asia` | SG, MY, TH, VN, ID, PH, MM, KH, LA, BN |
| `middle_east` | SA, AE, IL, TR, EG, IR, IQ, JO, KW, LB, QA, OM, BH, YE |
| `africa` | ZA, NG, EG, KE, MA, TN, GH, ET, CI, TZ, SN, UG, CM |
| `north_africa` | EG, MA, TN, LY, DZ, SD |
| `oceania` | AU, NZ, FJ, PG, WS, SB |

---

## Country Names (Portuguese / English accepted)

Country names can be specified as ISO codes or full names in Portuguese or English:

```bash
--dork-country BR
--dork-country brazil
--dork-country brasil
--dork-country "Sao Paulo"    # (this is --dork-city)
```

Accepted names include: brasil, brazil, argentina, mexico, colombia, chile, peru, venezuela, ecuador, bolivia, paraguay, uruguay, germany, france, italy, spain, portugal, and many more.

---

## Output Format

```
  ====================================================================
  Online Printer Discovery — Dork Mode
  Filter: vendors=epson,ricoh | regions=[AR,BO,BR,...] | ports=[LPD]
  Limit : 100 results per query
  ====================================================================

  [Shodan] 4 queries
    [1/4] Epson printers, AR/BO/BR/...
           Query: "EPSON" (country:AR OR country:BR ...) port:515
           Found: 47
    [2/4] Epson printers, AR/BO/BR/... (banner variant)
           Query: "Epson" (country:AR OR country:BR ...) port:515
           Found: 12
    ...

  ====================================================================
  Results — 73 unique printer(s) found
  ====================================================================
  IP               Port    CC  City              Org                           Src
  -----------------------------------------------------------------------
  177.x.x.x       LPD     BR  Sao Paulo         Claro NXT Telecomunicacoe..   shodan
  189.x.x.x       LPD     BR  Rio de Janeiro    Oi S.A.                       shodan
  190.x.x.x       LPD     AR  Buenos Aires      Telecom Argentina             shodan
  ...

  Distribution: BR:41  AR:18  CO:9  MX:5

  [+] Results saved to .log/discovery_20260325_143022.json
  [+] Next: python printer-reaper.py <IP> --scan
```

---

## How Shodan Dorks Are Built

| Parameter | Shodan syntax |
|-----------|--------------|
| `--dork-vendor epson` | `"EPSON"` |
| `--dork-country BR` | `country:BR` |
| `--dork-country BR --dork-country AR` | `(country:BR OR country:AR)` |
| `--dork-region latin_america` | `(country:AR OR country:BO OR country:BR ...)` |
| `--dork-city "Sao Paulo"` | `city:"Sao Paulo"` |
| `--dork-port 9100` | `port:9100` |
| `--dork-port 515 --dork-port 9100` | `(port:515 OR port:9100)` |
| `--dork-org "Telefonica"` | `org:"Telefonica"` |
| `--dork-model "pro 5500"` | `"pro 5500"` |

Combined example for `--dork-vendor hp --dork-country BR --dork-port 9100 --dork-city "Sao Paulo"`:
```
"HP LaserJet" country:BR city:"Sao Paulo" port:9100
```

## How Censys Dorks Are Built

| Parameter | Censys syntax |
|-----------|--------------|
| `--dork-vendor epson` | `services.banner="EPSON"` |
| `--dork-country BR` | `location.country_code="BR"` |
| `--dork-port 9100` | `services.port=9100` |
| `--dork-city "Sao Paulo"` | `location.city="Sao Paulo"` |
| `--dork-org "Telefonica"` | `autonomous_system.name="Telefonica"` |
| `--dork-cpe "cpe:/h:hp:..."` | `services.software.uniform_resource_identifier="..."` |

---

## Workflow After Discovery

```bash
# 1. Discover
python printer-reaper.py --discover-online --dork-vendor epson --dork-region latin_america

# 2. Scan individual result
python printer-reaper.py 177.X.X.X --scan

# 3. Auto exploit
python printer-reaper.py 177.X.X.X --auto-exploit

# 4. Brute-force login
python printer-reaper.py 177.X.X.X --bruteforce --bf-vendor epson
```
