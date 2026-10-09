def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_catalog(client):
    response = client.get("/api/v1/catalog")
    assert response.status_code == 200
    body = response.json()
    ids = {item["id"] for item in body["backends"]}
    assert {"splunk", "elasticsearch", "opensearch", "opensearch-ppl"}.issubset(ids)


def test_validate_valid_rule(client, sigma_rule):
    response = client.post("/api/v1/validate", json={"sigma": sigma_rule})
    assert response.status_code == 200
    assert response.json()["valid"] is True
    assert response.json()["rule_count"] == 1


def test_validate_invalid_rule(client):
    response = client.post("/api/v1/validate", json={"sigma": "title: [broken"})
    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert response.json()["errors"]


def test_convert_splunk(client, sigma_rule):
    response = client.post(
        "/api/v1/convert",
        json={
            "sigma": sigma_rule,
            "backend": "splunk",
            "pipelines": ["splunk_windows"],
            "format": "default",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["output"]
    assert "whoami" in str(body["output"]).lower()


def test_unknown_backend(client, sigma_rule):
    response = client.post(
        "/api/v1/convert",
        json={"sigma": sigma_rule, "backend": "nope", "format": "default"},
    )
    assert response.status_code == 400


def test_bad_format(client, sigma_rule):
    response = client.post(
        "/api/v1/convert",
        json={"sigma": sigma_rule, "backend": "splunk", "format": "not-a-format"},
    )
    assert response.status_code == 400
