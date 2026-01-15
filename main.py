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

    for name, dns in RESOLVERS.items():
        results[name] = dig_query(dns, domain)

    # ⬇️ WAJIB ADA DEFAULT VALUE
    status = "unknown"
    explanation = "Kondisi tidak dapat ditentukan"

    # Domain mati
    if not results["google"] and not results["cloudflare"]:
        status = "domain_unreachable"
        explanation = "Domain tidak dapat di-resolve oleh DNS publik"

    # DNS publik OK, tapi Nawala tidak terjangkau
    elif results["google"] and results["cloudflare"] and results["nawala"] is None:
        status = "nawala_unreachable"
        explanation = (
            "Server tidak dapat menjangkau DNS Nawala "
            "(kemungkinan bukan jaringan Indonesia)"
        )

    # Semua resolve
    elif results["google"] and results["cloudflare"] and results["nawala"]:
        status = "not_blocked"
        explanation = "Domain dapat diakses normal oleh semua DNS"

    # DNS publik resolve, Nawala reachable tapi kosong
    elif results["google"] and results["cloudflare"] and results["nawala"] == "":
        status = "suspected_blocked_isp"
        explanation = (
            "Domain ter-resolve di DNS publik namun tidak di DNS Nawala "
            "(indikasi blokir ISP)"
        )

    return {
        "domain": domain,
        "status": status,
        "explanation": explanation,
        "resolvers": results,
        "note": (
            "Ini bukan API resmi Nawala. "
            "Status ditentukan berdasarkan perbandingan hasil DNS resolver."
        )
    }

