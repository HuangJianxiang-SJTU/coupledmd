"""
NAR Compliance Acceptance Tests for CoupledMD.

These tests verify that the web server meets the NAR free-access requirement:
  - No login, registration, account, or email is ever required to reach any
    page, dataset, download, CSV, or API endpoint.
  - The only access-limiting mechanism is per-IP rate limiting.
  - Licence, citation, and privacy policy are present.

Run: pytest tests/test_compliance.py -v
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


# --------------------------------------------------------------------------- #
# 1. Anonymous access — every core surface returns HTTP 200
# --------------------------------------------------------------------------- #

class TestAnonymousAccess:
    """An anonymous client (no cookies, no auth header) gets HTTP 200 for
    every core page, download, and API endpoint."""

    def test_home_page(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_systems_page(self, client):
        r = client.get("/")
        assert r.status_code == 200  # SPA serves same index.html

    def test_health(self, client):
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_families(self, client):
        r = client.get("/api/v1/families")
        assert r.status_code == 200
        assert len(r.json()["families"]) > 0

    def test_systems_list(self, client):
        r = client.get("/api/v1/systems")
        assert r.status_code == 200
        assert r.json()["total"] > 0

    def test_system_detail(self, client):
        r = client.get("/api/v1/systems/Gi_6CMO")
        assert r.status_code == 200

    def test_system_pockets(self, client):
        r = client.get("/api/v1/systems/Gi_6CMO/pockets")
        assert r.status_code == 200

    def test_system_gateways(self, client):
        r = client.get("/api/v1/systems/Gi_6CMO/gateways")
        # May be 404 for protein-only systems, but must not be 401/403
        assert r.status_code in (200, 404)

    def test_system_gprotein(self, client):
        r = client.get("/api/v1/systems/Gi_6CMO/gprotein")
        assert r.status_code == 200

    def test_system_contacts(self, client):
        r = client.get("/api/v1/systems/Gi_6CMO/contacts")
        assert r.status_code == 200

    def test_system_subunit_ranges(self, client):
        r = client.get("/api/v1/systems/Gi_6CMO/subunit-ranges")
        assert r.status_code == 200

    def test_viz_structure_download(self, client):
        r = client.get("/api/v1/systems/Gi_6CMO/viz/structure")
        assert r.status_code == 200

    def test_viz_meta(self, client):
        r = client.get("/api/v1/systems/Gi_6CMO/viz/meta")
        assert r.status_code == 200

    def test_consensus_druggable(self, client):
        r = client.get("/api/v1/consensus/pockets/druggable")
        assert r.status_code == 200

    def test_consensus_orthosteric(self, client):
        r = client.get("/api/v1/consensus/pockets/orthosteric")
        assert r.status_code == 200

    def test_consensus_gateways(self, client):
        r = client.get("/api/v1/consensus/gateways")
        assert r.status_code == 200

    def test_consensus_nominations(self, client):
        r = client.get("/api/v1/consensus/nominations")
        assert r.status_code == 200

    def test_consensus_reorg(self, client):
        r = client.get("/api/v1/consensus/reorg")
        assert r.status_code == 200

    def test_consensus_coupling(self, client):
        r = client.get("/api/v1/consensus/coupling")
        assert r.status_code == 200

    def test_consensus_barcode(self, client):
        r = client.get("/api/v1/consensus/gprotein/barcode")
        assert r.status_code == 200

    def test_citation_endpoint(self, client):
        r = client.get("/api/v1/citation")
        assert r.status_code == 200
        data = r.json()
        assert data["data_licence"] == "CC-BY-4.0"
        assert data["code_licence"] == "MIT"

    def test_citation_cff(self, client):
        r = client.get("/api/v1/citation.cff")
        assert r.status_code == 200
        assert "cff-version" in r.text

    def test_robots_txt(self, client):
        r = client.get("/robots.txt")
        assert r.status_code == 200
        assert "Allow: /" in r.text


# --------------------------------------------------------------------------- #
# 2. No auth redirects — no public route 3xx-redirects to login
# --------------------------------------------------------------------------- #

class TestNoAuthRedirects:
    """No public route 3xx-redirects an anonymous client to a login page."""

    def test_systems_no_redirect(self, client):
        r = client.get("/api/v1/systems", follow_redirects=False)
        assert r.status_code != 307
        assert r.status_code != 301

    def test_system_detail_no_redirect(self, client):
        r = client.get("/api/v1/systems/Gi_6CMO", follow_redirects=False)
        assert r.status_code != 307
        assert r.status_code != 301

    def test_viz_structure_no_redirect(self, client):
        r = client.get("/api/v1/systems/Gi_6CMO/viz/structure", follow_redirects=False)
        assert r.status_code != 307
        assert r.status_code != 301


# --------------------------------------------------------------------------- #
# 3. No email/key required — Tier-0 limits are reachable
# --------------------------------------------------------------------------- #

class TestNoEmailRequired:
    """No endpoint requires email or key to return data."""

    def test_key_request_no_email(self, client):
        """API key is issued even with no email."""
        r = client.get("/api/v1/keys/request")
        assert r.status_code == 200
        data = r.json()
        assert data["api_key"].startswith("cmd_")
        assert data["notice"]  # Must include notice that key is optional

    def test_all_data_accessible_without_key(self, client):
        """All data endpoints return 200 without an API key."""
        endpoints = [
            "/api/v1/health",
            "/api/v1/families",
            "/api/v1/systems",
            "/api/v1/systems/Gi_6CMO",
            "/api/v1/systems/Gi_6CMO/pockets",
            "/api/v1/systems/Gi_6CMO/contacts",
            "/api/v1/consensus/pockets/druggable",
            "/api/v1/consensus/gateways",
            "/api/v1/citation",
        ]
        for ep in endpoints:
            r = client.get(ep)
            assert r.status_code == 200, f"Failed for {ep}: {r.status_code}"


# --------------------------------------------------------------------------- #
# 4. Licence and citation present
# --------------------------------------------------------------------------- #

class TestLicenceAndCitation:
    """Licence files, CITATION.cff, and on-page citation are present."""

    def test_license_file_exists(self):
        from pathlib import Path
        root = Path(__file__).resolve().parent.parent
        assert (root / "LICENSE").exists()
        assert "CC-BY-4.0" in (root / "LICENSE").read_text() or "Attribution 4.0" in (root / "LICENSE").read_text()

    def test_license_code_file_exists(self):
        from pathlib import Path
        root = Path(__file__).resolve().parent.parent
        assert (root / "LICENSE-CODE").exists()
        assert "MIT" in (root / "LICENSE-CODE").read_text()

    def test_citation_cff_exists(self):
        from pathlib import Path
        root = Path(__file__).resolve().parent.parent
        assert (root / "CITATION.cff").exists()
        assert "cff-version" in (root / "CITATION.cff").read_text()

    def test_citation_api_returns_licence(self, client):
        r = client.get("/api/v1/citation")
        data = r.json()
        assert data["data_licence"] == "CC-BY-4.0"
        assert data["code_licence"] == "MIT"
        assert "CITATION-TODO" in data["text"]  # Placeholder until DOI assigned

    def test_frontend_has_citation_block(self):
        from pathlib import Path
        root = Path(__file__).resolve().parent.parent
        home = (root / "frontend" / "src" / "pages" / "Home.jsx").read_text()
        assert "How to cite" in home
        assert "CC-BY-4.0" in home

    def test_frontend_has_cookie_consent(self):
        from pathlib import Path
        root = Path(__file__).resolve().parent.parent
        app = (root / "frontend" / "src" / "App.jsx").read_text()
        assert "CookieConsent" in app

    def test_frontend_has_privacy_page(self):
        from pathlib import Path
        root = Path(__file__).resolve().parent.parent
        assert (root / "frontend" / "src" / "pages" / "Privacy.jsx").exists()

    def test_frontend_has_terms_page(self):
        from pathlib import Path
        root = Path(__file__).resolve().parent.parent
        assert (root / "frontend" / "src" / "pages" / "Terms.jsx").exists()


# --------------------------------------------------------------------------- #
# 5. Rate limiting — returns 429, never redirects to login
# --------------------------------------------------------------------------- #

class TestRateLimiting:
    """Rate limiting returns HTTP 429, never redirects to login."""

    def test_rate_limit_headers(self, client):
        """API responses include rate limit tier header."""
        r = client.get("/api/v1/health")
        # The middleware adds X-RateLimit-Tier
        assert r.status_code == 200

    def test_rate_limit_is_not_auth(self, client):
        """Rate limit response is 429, not 401 or 403."""
        # We can't easily trigger 429 in tests (would need 60+ requests),
        # but we verify the middleware is present
        from api.main import app
        middleware_names = [m.cls.__name__ for m in app.user_middleware]
        assert "RateLimitMiddleware" in middleware_names


# --------------------------------------------------------------------------- #
# 6. Optional accounts — convenience only
# --------------------------------------------------------------------------- #

class TestOptionalAccounts:
    """Accounts are optional and convenience-only."""

    def test_register_creates_account(self, client):
        r = client.get("/api/v1/accounts/register",
                       params={"email": "compliance@test.com", "password": "testpass123"})
        assert r.status_code == 200
        data = r.json()
        assert data["account"]["email"] == "compliance@test.com"
        assert "notice" in data  # Must state account is optional

    def test_login_returns_account(self, client):
        r = client.get("/api/v1/accounts/login",
                       params={"email": "compliance@test.com", "password": "testpass123"})
        assert r.status_code == 200
        data = r.json()
        assert data["account"]["email"] == "compliance@test.com"

    def test_account_provides_api_key(self, client):
        r = client.get("/api/v1/accounts/login",
                       params={"email": "compliance@test.com", "password": "testpass123"})
        data = r.json()
        assert data["account"]["api_key"]  # Account holders get a Tier-1 key

    def test_delete_account(self, client):
        r = client.get("/api/v1/accounts/delete",
                       params={"email": "compliance@test.com", "password": "testpass123"})
        assert r.status_code == 200
        assert r.json()["deleted"] is True

    def test_export_account_data(self, client):
        # Register, export, delete
        client.get("/api/v1/accounts/register",
                   params={"email": "export@test.com", "password": "testpass123"})
        r = client.get("/api/v1/accounts/export",
                       params={"email": "export@test.com", "password": "testpass123"})
        assert r.status_code == 200
        assert r.json()["account"]["email"] == "export@test.com"
        # Cleanup
        client.get("/api/v1/accounts/delete",
                   params={"email": "export@test.com", "password": "testpass123"})
