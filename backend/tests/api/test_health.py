"""Smoke tests for /health and /metrics endpoints.

These tests require the test docker-compose stack to be running:
    docker compose -f docker-compose.test.yml up -d
"""


async def test_health_returns_200_or_503(client):
    """Health endpoint must respond; 200 when all critical services ok, 503 otherwise."""
    response = await client.get("/health")
    assert response.status_code in (200, 503)


async def test_health_response_schema(client):
    """Health response must contain status and all service keys with valid values."""
    response = await client.get("/health")
    data = response.json()

    assert "status" in data
    assert data["status"] in ("ok", "degraded")

    for key in ("postgres", "redis", "qdrant", "minio", "worker"):
        assert key in data, f"missing key: {key}"
        assert data[key] in ("ok", "degraded"), f"unexpected value for {key}: {data[key]}"


async def test_health_postgres_ok(client):
    """Postgres must be healthy when the test stack is running."""
    response = await client.get("/health")
    data = response.json()
    assert data["postgres"] == "ok"


async def test_metrics_returns_prometheus_format(client):
    """Metrics endpoint must return Prometheus text format with HELP comments."""
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert b"# HELP" in response.content
