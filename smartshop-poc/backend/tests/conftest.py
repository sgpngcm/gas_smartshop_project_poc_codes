import os
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

TEST_PASSWORD = os.getenv("TEST_PASSWORD", "Passw0rd!123")

# --- Your REAL endpoints from URL dump ---
CHAT_URL = "/api/assistant/chat/"
RESET_URL = "/api/assistant/reset/"
SMART_SEARCH_URL = "/api/ai/smart-search/"
RECO_URL = "/api/ai/recommendations/"
INSIGHTS_URL = "/api/ai/insights/"  # optional

LOGIN_URL = "/api/auth/login/"
REGISTER_URL = "/api/auth/register/"

AUTH_MODE = os.getenv("TEST_AUTH_MODE", "jwt")  # jwt | session | none


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def endpoints():
    return {
        "chat": "/api/assistant/chat/",
        "reset": "/api/assistant/reset/",
        "smart_search": "/api/ai/smart-search/",
        "reco": "/api/ai/recommendations/",
        "insights": "/api/ai/insights/",
        "login": "/api/auth/login/",
        "register": "/api/auth/register/",
    }



@pytest.fixture
def user(db):
    User = get_user_model()
    fields = {f.name for f in User._meta.fields}

    kwargs = {}
    if "username" in fields:
        kwargs["username"] = "testuser"
    if "email" in fields:
        kwargs["email"] = "testuser@example.com"

    # create_user signature can differ; handle safely
    u = User.objects.create_user(**kwargs, password=TEST_PASSWORD)
    return u


@pytest.fixture
def auth_client(api_client, user, endpoints):
    """
    Auth client for your POC:
    - jwt: calls /api/auth/login/ and sets Authorization: Bearer <token>
    - session: force_login
    - none: no auth
    """
    if AUTH_MODE == "none":
        return api_client

    if AUTH_MODE == "session":
        api_client.force_login(user)
        return api_client

    # JWT-style: try username then email
    payloads = []
    if hasattr(user, "username") and user.username:
        payloads.append({"username": user.username, "password": TEST_PASSWORD})
    if hasattr(user, "email") and user.email:
        payloads.append({"email": user.email, "password": TEST_PASSWORD})

    # Try login
    for payload in payloads:
        resp = api_client.post(endpoints["login"], payload, format="json")
        if resp.status_code in (200, 201):
            data = resp.json()
            token = data.get("access") or data.get("token") or data.get("access_token")
            assert token, f"Login succeeded but token missing. Response keys: {list(data.keys())}"
            api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
            return api_client

    # If login failed, fall back to session (some POCs use cookies instead)
    try:
        api_client.force_login(user)
    except Exception:
        pass

    return api_client


@pytest.fixture
def mock_ai(monkeypatch):
    """
    Optional: prevent hitting real AI provider.
    Patch common function names used in your POC.
    If your project uses a different module/function, tell me the import path and I’ll adjust.
    """
    fake_text = "Mocked assistant reply."
    fake_json = {
        "recommendations": [{"product_id": 1, "reason": "Mocked reason"}],
        "intent": {"keywords": ["wireless", "earbuds"], "max_price": 100},
        "summary": "Mocked summary",
    }

    patched = False

    candidates = [
        ("smartshop.ai", "call_ai"),
        ("smartshop.ai_service", "call_ai"),
        ("smartshop.services.ai", "call_ai"),
        ("smartshop.services.openai", "call_ai"),
        ("smartshop.services.gemini", "call_ai"),
        ("smartshop.views", "call_ai"),
        ("smartshop.api", "call_ai"),
        ("ai.services", "call_ai"),
    ]

    def _fake_call_ai(*args, **kwargs):
        # Return string; many endpoints parse/format downstream
        return str(fake_json)

    for mod_path, fn in candidates:
        try:
            mod = __import__(mod_path, fromlist=[fn])
            if hasattr(mod, fn):
                monkeypatch.setattr(mod, fn, _fake_call_ai)
                patched = True
        except Exception:
            continue

    return patched
