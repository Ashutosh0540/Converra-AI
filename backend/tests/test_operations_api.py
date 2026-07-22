def test_operational_endpoints_expose_health_version_and_metrics(client):
    assert client.get("/health/live").json() == {"status": "live"}
    assert client.get("/health/ready").json() == {"status": "ready"}
    version = client.get("/version")
    assert version.status_code == 200
    assert "version" in version.json()
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "converra_http_requests_total" in metrics.text


def test_operational_responses_include_request_and_security_headers(client):
    response = client.get("/health/live")
    assert response.headers["x-request-id"]
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
