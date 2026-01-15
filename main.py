from fastapi import FastAPI, Query
import dns.resolver
import requests

app = FastAPI(
    title="Nawala / ISP DNS Checker API",
    description="Cek status domain via DNS ISP + Relay Indonesia",
    version="1.0.0"
)

# ===============================
# KONFIGURASI
# ===============================

DNS_ISP = {
    "telkom": "202.134.1.10",
    "indihome": "202.134.0.155",
    "biznet": "202.134.0.62"
}

RELAY_URL = "http://103.146.202.228:4000/resolve"

# ===============================
# DNS ISP CHECK (LOKAL)
# ===============================

def resolve_isp(domain: str):
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

# ===============================
# RELAY CHECK (INDONESIA)
# ===============================

def relay_check(domain: str):
    try:
        r = requests.post(
            RELAY_URL,
            json={"domain": domain},
            timeout=3
        )
        return r.json()
    except Exception:
        return {
            "status": "UNREACHABLE"
        }

# ===============================
# ENDPOINT UTAMA
# ===============================

@app.get("/check")
def check_domain(domain: str = Query(..., description="Domain yang akan dicek")):

    isp_results = resolve_isp(domain)
    relay_result = relay_check(domain)

    open_count = sum(1 for r in isp_results.values() if r["status"] == "OPEN")
    blocked_count = sum(1 for r in isp_results.values() if r["status"] == "BLOCKED")

    # ===============================
    # LOGIKA FINAL STATUS
    # ===============================

    if relay_result.get("status") == "OPEN":
        final_status = "NOT_BLOCKED"
        explanation = "Relay Indonesia berhasil resolve domain"

    elif blocked_count == len(isp_results):
        final_status = "SUSPECTED_BLOCKED_ISP"
        explanation = "Domain diblokir oleh seluruh DNS ISP yang diuji"

    elif open_count > 0:
        final_status = "NOT_BLOCKED"
        explanation = "Domain dapat diakses oleh sebagian DNS ISP"

    else:
        final_status = "UNKNOWN"
        explanation = "Tidak ada respon DNS yang meyakinkan"

    return {
        "domain": domain,
        "status": final_status,
        "explanation": explanation,
        "isp_results": isp_results,
        "relay_indonesia": relay_result,
        "note": "Ini bukan API resmi Nawala, hanya indikasi berbasis DNS"
    }
