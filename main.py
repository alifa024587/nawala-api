from fastapi import FastAPI, Query
import dns.resolver

app = FastAPI(title="Nawala Checker API")

DNS_ISP = [
    "202.134.1.10",   # Telkom
    "202.134.0.155",  # Indihome
    "202.134.0.62"    # Biznet
]

def check_domain(domain):
    for dns_ip in DNS_ISP:
        try:
            r = dns.resolver.Resolver()
            r.nameservers = [dns_ip]
            r.timeout = 2
            r.lifetime = 2

            ans = r.resolve(domain, "A")
            ips = [a.address for a in ans]

            return {
                "status": "OPEN",
                "dns": dns_ip,
                "ips": ips
            }

        except dns.resolver.NXDOMAIN:
            return {
                "status": "BLOCKED",
                "dns": dns_ip,
                "reason": "NXDOMAIN"
            }
        except Exception:
            continue

    return {
        "status": "UNKNOWN",
        "reason": "NO DNS RESPONSE"
    }

@app.get("/check")
def check_domain(domain: str = Query(...)):
    results = {}
    ...
    return {
        "domain": domain,
        "status": status,
        "explanation": explanation,
        "resolvers": results,
        "note": "Ini bukan API resmi Nawala..."
    }


