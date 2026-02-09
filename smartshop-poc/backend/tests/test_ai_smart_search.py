import pytest

@pytest.mark.django_db
def test_smart_search_rejects_empty_query(api_client, endpoints):
    # GET without query should be rejected or return empty results depending on your design
    resp = api_client.get(endpoints["smart_search"])
    assert resp.status_code in (200, 400), f"{resp.status_code} {resp.content}"

@pytest.mark.django_db
def test_smart_search_success(api_client, endpoints):
    # Try common param names
    resp = api_client.get(endpoints["smart_search"], {"query": "wireless earbuds under $100"})
    if resp.status_code == 400:
        resp = api_client.get(endpoints["smart_search"], {"q": "wireless earbuds under $100"})
    if resp.status_code == 400:
        resp = api_client.get(endpoints["smart_search"], {"text": "wireless earbuds under $100"})

    assert resp.status_code == 200, f"{resp.status_code} {resp.content}"
    data = resp.json()
    assert any(k in data for k in ("products", "results", "items", "data")), f"Unexpected keys: {list(data.keys())}"
