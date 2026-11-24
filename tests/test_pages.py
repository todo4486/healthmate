"""Basic checks that the app starts and its pages respond."""


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"HealthMate" in response.data


def test_health_check_returns_ok(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "app": "HealthMate"}


def test_unknown_page_returns_404(client):
    assert client.get("/this-page-does-not-exist").status_code == 404


def test_test_config_is_used(app):
    assert app.config["TESTING"] is True
    assert app.config["APP_ENV"] == "testing"
