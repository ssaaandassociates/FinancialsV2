"""
Multi-tenant isolation test (Slice 0b).
Simulates two firms via Supabase-style JWTs and proves data isolation.
"""
import os, jwt, datetime, uuid

# Set a known JWT secret BEFORE importing the app
TEST_SECRET = "test-jwt-secret-for-tenancy-verification-only"
os.environ["SUPABASE_JWT_SECRET"] = TEST_SECRET

from fastapi.testclient import TestClient
from app.main import app

PASS = FAIL = 0
def check(label, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1; print(f"  [PASS] {label}")
    else:
        FAIL += 1; print(f"  [FAIL] {label}  {detail}")

def make_token(uid, email):
    """Forge a valid Supabase-style token signed with our test secret."""
    payload = {
        "sub": uid,
        "email": email,
        "aud": "authenticated",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
    }
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")

print("=" * 60)
print("MULTI-TENANT ISOLATION TEST")
print("=" * 60)

with TestClient(app) as c:
    # Two separate users = two separate firms
    uid_a, uid_b = str(uuid.uuid4()), str(uuid.uuid4())
    tok_a = make_token(uid_a, "alice@firma.com")
    tok_b = make_token(uid_b, "bob@firmb.com")
    hdr_a = {"Authorization": f"Bearer {tok_a}"}
    hdr_b = {"Authorization": f"Bearer {tok_b}"}

    # 1. No token → rejected
    r = c.get("/api/clients/")
    check("Request without token is rejected", r.status_code == 401, f"got {r.status_code}")

    # 2. Bad token → rejected
    r = c.get("/api/clients/", headers={"Authorization": "Bearer garbage.token.here"})
    check("Invalid token is rejected", r.status_code == 401, f"got {r.status_code}")

    # 3. Firm A creates a client
    r = c.post("/api/clients/", headers=hdr_a, json={"name": "Firm A Client 1"})
    check("Firm A can create client", r.status_code == 200, r.text[:120])
    a_client_id = r.json().get("id")

    # 4. Firm B creates a client
    r = c.post("/api/clients/", headers=hdr_b, json={"name": "Firm B Client 1"})
    check("Firm B can create client", r.status_code == 200, r.text[:120])
    b_client_id = r.json().get("id")

    # 5. Firm A sees ONLY its own client
    r = c.get("/api/clients/", headers=hdr_a)
    a_list = r.json()
    a_names = [x["name"] for x in a_list]
    check("Firm A sees its own client", "Firm A Client 1" in a_names)
    check("Firm A does NOT see Firm B's client", "Firm B Client 1" not in a_names,
          f"leak! A sees: {a_names}")

    # 6. Firm B sees ONLY its own client
    r = c.get("/api/clients/", headers=hdr_b)
    b_names = [x["name"] for x in r.json()]
    check("Firm B sees its own client", "Firm B Client 1" in b_names)
    check("Firm B does NOT see Firm A's client", "Firm A Client 1" not in b_names,
          f"leak! B sees: {b_names}")

    # 7. Firm B cannot fetch Firm A's client by guessing its ID
    r = c.get(f"/api/clients/{a_client_id}", headers=hdr_b)
    check("Firm B cannot fetch Firm A's client by ID", r.status_code == 404,
          f"got {r.status_code} — ISOLATION BREACH" if r.status_code == 200 else "")

    # 8. Firm A CAN fetch its own client by ID
    r = c.get(f"/api/clients/{a_client_id}", headers=hdr_a)
    check("Firm A can fetch its own client by ID", r.status_code == 200, f"got {r.status_code}")

    # 9. Firm B cannot update Firm A's client
    r = c.put(f"/api/clients/{a_client_id}", headers=hdr_b, json={"name": "HACKED"})
    check("Firm B cannot update Firm A's client", r.status_code == 404,
          f"got {r.status_code} — ISOLATION BREACH" if r.status_code == 200 else "")

print("=" * 60)
print(f"RESULTS: {PASS} PASSED, {FAIL} FAILED")
print("=" * 60)
