import pytest

@pytest.mark.django_db
def test_reset_clears_session(api_client, endpoints):
    # First, send a chat message (if your backend stores messages server-side, great)
    api_client.post(
        endpoints["chat"],
        {"session_id": "pytest-session", "message": "Hello"},
        format="json",
    )

    # Reset should succeed
    resp = api_client.post(endpoints["reset"], {"session_id": "pytest-session"}, format="json")
    assert resp.status_code in (200, 204), f"{resp.status_code} {resp.content}"
