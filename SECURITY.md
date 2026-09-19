# Security Policy — PrinterXPL-Forge

**Language:** **English (en-US)** — default.

## Supported scope

- **In scope:** flaws in **PrinterXPL-Forge itself** (Python code, declared dependencies, printer modules) affecting the **operator** (RCE on the analyst machine, unsafe input handling, etc.).
- **Out of scope:** vulnerabilities found in target printers while using the framework; report those through the vendor.
- **Functional scope:** all PJL, PCL, PostScript, IPP, LPD, spooler, and printer firmware modules are in scope.

## Reporting a vulnerability

1. Use GitHub **private vulnerability reporting**: **Security → Report a vulnerability** on `mrhenrike/PrinterXPL-Forge`.
2. Do not file a public issue with a full exploit before triage.
3. Include:
   - Affected commit or tag
   - Minimal reproduction steps
   - Impact (confidentiality, integrity, availability)
   - Suggested patch (optional)

Alternatively, contact: **security.research@uniaogeek.com.br**

## Response targets (best effort)

| Phase | Target |
|-------|--------|
| Acknowledgement | ~72 hours |
| Initial triage | ~7 business days |
| Fix | depends on severity and complexity |

## Coordinated disclosure

We prefer **coordinated disclosure**: keep details private until a fix or agreed timeline.

## Safe use (operator responsibility)

- Use only on printers and print servers you **own** or have **written authorization** to test.
- Do not submit customer data or credentials to this repository.

## Conduct

Harassment or abuse in project channels: see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
