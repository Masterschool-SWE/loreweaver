"""End-to-end smoke test for v2 (agent calls are mocked — no API key needed)."""
import uuid

import pytest

from app.agent import service
from app.agent.structured import Encounter


@pytest.fixture(autouse=True)
def _mock_agent(monkeypatch):
    monkeypatch.setattr(
        service, "invoke_keeper",
        lambda session, hero, message, **kwargs: f"[mocked Keeper] {hero.name}: {message}",
    )
    monkeypatch.setattr(
        service, "forge_encounter",
        lambda hero, scene, **kwargs: Encounter(
            title="Ambush at the Bog", narrative="Mist coils around you.",
            monster_name="Mirewight", challenge_rating=2,
            suggested_tactics="Sing the song of apology.", loot=["Waystone"],
        ),
    )


def _auth(client):
    username = f"tester_{uuid.uuid4().hex[:8]}"
    client.post("/auth/register", json={"username": username, "password": "pw123456"})
    r = client.post("/auth/login", data={"username": username, "password": "pw123456"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_chat_and_encounter(client):
    headers = _auth(client)
    r = client.post("/heroes", json={"name": "Testhero", "char_class": "Mage"}, headers=headers)
    hero_id = r.json()["id"]

    r = client.post("/agent/invoke", json={"hero_id": hero_id, "message": "Hail!"}, headers=headers)
    assert r.status_code == 200
    assert "mocked Keeper" in r.json()["reply"]

    r = client.post("/agent/encounter", json={"hero_id": hero_id, "scene": "a foggy bog"}, headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["monster_name"] == "Mirewight" and body["challenge_rating"] == 2
