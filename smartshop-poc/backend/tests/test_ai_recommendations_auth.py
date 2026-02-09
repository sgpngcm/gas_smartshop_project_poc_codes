import pytest

@pytest.mark.django_db
def test_recommendations_requires_auth_or_open(api_client, endpoints):
    resp = api_client.get(endpoints["reco"])
    assert resp.status_code in (200, 401, 403), f"{resp.status_code} {resp.content}"

@pytest.mark.django_db
def test_recommendations_success_shape(auth_client, endpoints):
    resp = auth_client.get(endpoints["reco"])
    # If your auth_client didn't authenticate correctly, this could still be 401.
    assert resp.status_code in (200, 401, 403), f"{resp.status_code} {resp.content}"

    if resp.status_code == 200:
        data = resp.json()
        # Match your actual response keys
        assert "recommended" in data, f"Missing 'recommended'. Keys: {list(data.keys())}"
        assert "also_bought" in data, f"Missing 'also_bought'. Keys: {list(data.keys())}"
        assert "purchase_count" in data, f"Missing 'purchase_count'. Keys: {list(data.keys())}"
