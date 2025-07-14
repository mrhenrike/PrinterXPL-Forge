import requests

def check_shodan(ip):
    try:
        r = requests.get(f"https://www.shodan.io/host/{ip}", timeout=5)
        if "printer" in r.text.lower():
            return True
    except:
        pass
    return False

def check_google(ip):
    url = f"https://www.google.com/search?q=ip:{ip}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        return "printer" in r.text.lower()
    except:
        return False

def osint_check(ip):
    print(f"[*] Executando OSINT passivo para {ip}")
    results = {
        "shodan": check_shodan(ip),
        "google": check_google(ip)
    }
    return results
