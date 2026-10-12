"""AI endpoint-এ rate limit: সীমা পেরোলে 429, অন্য endpoint প্রভাবিত নয়।"""


def test_rate_limit_blocks_after_limit(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "3")
    # ফাঁকা body -> 422, কিন্তু middleware আগেই গণনা করে; Claude কল হয় না
    codes = [client.post("/api/cover-letter/generate", json={}).status_code for _ in range(5)]
    assert codes[:3] == [422, 422, 422]
    assert codes[3:] == [429, 429]
    r = client.post("/api/cover-letter/generate", json={})
    assert "Retry-After" in r.headers
    # সীমিত নয় এমন endpoint ঠিক থাকে
    assert client.get("/api/health").status_code == 200


def test_rate_limit_disabled_by_default_in_tests(client):
    codes = {client.post("/api/cover-letter/generate", json={}).status_code for _ in range(15)}
    assert codes == {422}
