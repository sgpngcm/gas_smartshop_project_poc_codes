import pytest

@pytest.mark.django_db
def test_chat_rejects_empty_message(api_client, endpoints):
    resp = api_client.post(endpoints["chat"], {"message": ""}, format="json")
    assert resp.status_code in (400, 422), f"{resp.status_code} {resp.content}"

@pytest.mark.django_db
def test_chat_success(api_client, endpoints, mock_ai):
    resp = api_client.post(
        endpoints["chat"],
        {"session_id": "pytest-session", "message": "Recommend me headphones under $80"},
        format="json",
    )
    assert resp.status_code in (200, 201), f"{resp.status_code} {resp.content}"
    data = resp.json()
    assert any(k in data for k in ("reply", "message", "content", "assistant", "messages")), f"Unexpected keys: {list(data.keys())}"
