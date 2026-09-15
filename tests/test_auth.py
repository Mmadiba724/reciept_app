import pytest

pytestmark = pytest.mark.asyncio


async def test_signup_creates_tenant_and_user(client, monkeypatch):
    monkeypatch.setattr("app.api.auth.send_verification_email", lambda **kwargs: {"MessageID": "fake"})

    response = await client.post(
        "/auth/signup",
        json={
            "business_name": "Acme Rentals",
            "full_name": "Jane Landlord",
            "email": "jane@example.com",
            "password": "supersecret",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "jane@example.com"
    assert "tenant_id" in body
    assert "user_id" in body


async def test_signup_duplicate_email_conflicts(client, monkeypatch):
    monkeypatch.setattr("app.api.auth.send_verification_email", lambda **kwargs: {"MessageID": "fake"})

    payload = {
        "business_name": "Acme Rentals",
        "full_name": "Jane Landlord",
        "email": "dup@example.com",
        "password": "supersecret",
    }
    first = await client.post("/auth/signup", json=payload)
    assert first.status_code == 201

    second = await client.post("/auth/signup", json=payload)
    assert second.status_code == 409


async def test_login_requires_correct_password(client, monkeypatch):
    monkeypatch.setattr("app.api.auth.send_verification_email", lambda **kwargs: {"MessageID": "fake"})

    await client.post(
        "/auth/signup",
        json={
            "business_name": "Acme Rentals",
            "full_name": "Jane Landlord",
            "email": "login@example.com",
            "password": "supersecret",
        },
    )

    bad = await client.post("/auth/login", json={"email": "login@example.com", "password": "wrong"})
    assert bad.status_code == 401

    good = await client.post("/auth/login", json={"email": "login@example.com", "password": "supersecret"})
    assert good.status_code == 200
    assert "access_token" in good.json()


async def test_verify_email_with_token(client, monkeypatch):
    captured = {}

    def fake_send(*, to_email, verify_url):
        captured["url"] = verify_url
        return {"MessageID": "fake"}

    monkeypatch.setattr("app.api.auth.send_verification_email", fake_send)

    await client.post(
        "/auth/signup",
        json={
            "business_name": "Acme Rentals",
            "full_name": "Jane Landlord",
            "email": "verify@example.com",
            "password": "supersecret",
        },
    )

    token = captured["url"].split("token=")[1]
    response = await client.post("/auth/verify", json={"token": token})
    assert response.status_code == 200
