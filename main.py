from fastapi import FastAPI, Query
import dns.resolver

app = FastAPI(
    title="Nawala / ISP DNS Checker API",
    description="Cek status domain menggunakan DNS ISP Indonesia",
    version="1.0.0"
)

DNS_ISP = {
    "telkom": "202.134.1.10",
    "indihome": "202.134.0.155",
    "biznet": "202.134.0.62"
}

def resolve_domain(domain: str):
    results = {}

    for isp, dns_ip in DNS_ISP.items():
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [dns_ip]
            resolver.timeout = 2
            resolver.lifetime = 2

            answer = resolver.resolve(domain, "A")
            ips = [r.address for r in answer]

            results[isp] = {
                "status": "OPEN",
                "ips": ips
            }

        except dns.resolver.NXDOMAIN:
            results[isp] = {
                "status": "BLOCKED",
                "reason": "NXDOMAIN"
            }

        except Exception:
            results[isp] = {
                "status": "NO_RESPONSE"
            }

    return results


@app.get("/check")
def check(domain: str = Query(..., description="Domain yang akan dicek")):
    results = resolve_domain(domain)

    # ANALISIS STATUS GLOBAL
    open_count = sum(1 for r in results.values() if r["status"] == "OPEN")
    blocked_count = sum(1 for r in results.values() if r["status"] == "BLOCKED")

    if open_count > 0:
        final_status = "NOT_BLOCKED"
        explanation = "Domain dapat di-resolve oleh setidaknya satu DNS ISP"
    elif blocked_count == len(results):
        final_status = "SUSPECTED_BLOCKED_ISP"
        explanation = "Domain diblokir oleh seluruh DNS ISP yang diuji"
    else:
        final_status = "UNKNOWN"
        explanation = "Tidak ada respon DNS yang meyakinkan"

    return {
        "domain": domain,
        "status": final_status,
        "explanation": explanation,
        "isp_results": results,
        "note": "Ini bukan API resmi Nawala, hanya indikasi berbasis DNS ISP"
    }
