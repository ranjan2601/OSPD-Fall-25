import sys
import types
import importlib
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    """
    Build a TestClient for the FastAPI router, while injecting a fake
    mail_client_api.get_client BEFORE api.py is imported (to avoid
    NotImplementedError during import).
    """
    # Fake module to satisfy
    fake_mod = types.ModuleType("mail_client_api")

    def fake_get_client(*, interactive: bool = False):
        # one fake message object with attrs used by api.py
        msg = types.SimpleNamespace(id="m1", subject="Hello", from_="a@x.com", body="Test")
        fake = types.SimpleNamespace()
        fake.get_messages = lambda max_results=10: [msg]
        fake.get_message = lambda message_id: msg if message_id == "m1" else (_ for _ in ()).throw(KeyError("not found"))
        fake.delete_message = lambda message_id: True if message_id == "m1" else (_ for _ in ()).throw(KeyError("not found"))
        fake.mark_as_read = lambda message_id: True if message_id == "m1" else (_ for _ in ()).throw(KeyError("not found"))
        return fake

    fake_mod.get_client = fake_get_client
    sys.modules["mail_client_api"] = fake_mod

    #  import of api.py after patching
    sys.modules.pop("mail_client_service.api", None)
    import mail_client_service.api as api

    app = FastAPI()
    app.include_router(api.router)
    return TestClient(app)


@pytest.fixture
def api_module(client):
    """
    Provide the imported api module (after the fake client is installed),
    so we can monkeypatch api.mail_client methods in branch tests.
    """
    import mail_client_service.api as api

    return api


# GET /messages
def test_get_messages_success(client: TestClient):
    r = client.get("/messages")
    assert r.status_code == 200
    data = r.json()
    assert "messages" in data
    assert data["messages"][0]["id"] == "m1"
    assert data["messages"][0]["sender"] == "a@x.com"


def test_get_messages_empty(client, api_module, monkeypatch):
    monkeypatch.setattr(api_module.mail_client, "get_messages", lambda max_results=10: [])
    r = client.get("/messages")
    assert r.status_code == 200
    assert r.json()["messages"] == []


def test_get_messages_500(client, api_module, monkeypatch):
    def boom(*_a, **_k):
        raise Exception("boom")

    monkeypatch.setattr(api_module.mail_client, "get_messages", boom)
    r = client.get("/messages")
    assert r.status_code == 500


# GET /messages/{message_id}
def test_get_message_ok(client):
    r = client.get("/messages/m1")
    assert r.status_code == 200
    body = r.json()
    assert "message" in body and body["message"]["id"] == "m1"


def test_get_message_not_found(client):
    r = client.get("/messages/does-not-exist")
    assert r.status_code == 404


def test_get_message_500(client, api_module, monkeypatch):
    def boom(_id):
        raise Exception("kaboom")

    monkeypatch.setattr(api_module.mail_client, "get_message", boom)
    r = client.get("/messages/m1")
    assert r.status_code == 500


#  DELETE /messages/{message_id}
def test_delete_message_ok(client):
    r = client.delete("/messages/m1")
    assert r.status_code == 200
    assert r.json()["status"] == "Deleted"


def test_delete_message_not_found(client, api_module, monkeypatch):
    def not_found(_id):
        raise KeyError("nf")

    monkeypatch.setattr(api_module.mail_client, "delete_message", not_found)
    r = client.delete("/messages/does-not-exist")
    assert r.status_code == 404


def test_delete_message_failed_returns_500(client, api_module, monkeypatch):
    # API treats False as failure -> 500
    monkeypatch.setattr(api_module.mail_client, "delete_message", lambda _id: False)
    r = client.delete("/messages/m1")
    assert r.status_code == 500


def test_delete_message_500(client, api_module, monkeypatch):
    def boom(_id):
        raise Exception("boom")

    monkeypatch.setattr(api_module.mail_client, "delete_message", boom)
    r = client.delete("/messages/m1")
    assert r.status_code == 500


#  POST /messages/{message_id}/mark-as-read
def test_mark_as_read_ok(client):
    r = client.post("/messages/m1/mark-as-read")
    assert r.status_code == 200
    assert r.json()["status"] == "Marked as read"


def test_mark_as_read_not_found(client, api_module, monkeypatch):
    def not_found(_id):
        raise KeyError("nf")

    monkeypatch.setattr(api_module.mail_client, "mark_as_read", not_found)
    r = client.post("/messages/does-not-exist/mark-as-read")
    assert r.status_code == 404


def test_mark_as_read_failed_returns_500(client, api_module, monkeypatch):
    monkeypatch.setattr(api_module.mail_client, "mark_as_read", lambda _id: False)
    r = client.post("/messages/m1/mark-as-read")
    assert r.status_code == 500


def test_mark_as_read_500(client, api_module, monkeypatch):
    def boom(_id):
        raise Exception("boom")

    monkeypatch.setattr(api_module.mail_client, "mark_as_read", boom)
    r = client.post("/messages/m1/mark-as-read")
    assert r.status_code == 500


# extra coverage on import-time branches and modules
def test_api_import_fallback_to_mock_client(monkeypatch):
    """
    Cover the import-time branch where get_client raises a RuntimeError
    containing 'No valid credentials found' and api.py builds a MockClient.
    """
    import sys, types, importlib

    fake_mod = types.ModuleType("mail_client_api")

    def raising_get_client(*, interactive: bool = False):
        raise RuntimeError("No valid credentials found for testing")

    fake_mod.get_client = raising_get_client
    sys.modules["mail_client_api"] = fake_mod

    sys.modules.pop("mail_client_service.api", None)
    import mail_client_service.api as api

    # Confirm fallback client is present and usable
    msgs = list(api.mail_client.get_messages())
    assert len(msgs) >= 1
    assert hasattr(msgs[0], "id")


def test_api_import_rethrows_other_runtimeerror(monkeypatch):
    """
    Cover the 'else: raise' path in the import-time try/except.
    """
    import sys, types, importlib

    fake_mod = types.ModuleType("mail_client_api")

    def raising_get_client(*, interactive: bool = False):
        raise RuntimeError("some other runtime error")  # triggers 'else: raise'

    fake_mod.get_client = raising_get_client
    sys.modules["mail_client_api"] = fake_mod

    sys.modules.pop("mail_client_service.api", None)
    with pytest.raises(RuntimeError):
        importlib.import_module("mail_client_service.api")


def test_import_main_for_coverage(client):
    """
    Import mail_client_service.main so its top-level code is executed.
    Depends on 'client' fixture so the fake mail_client_api is already installed.
    """
    import mail_client_service.main


def test_import_test_module_for_coverage(client):
    """
    Import mail_client_service.test so its top-level code is executed.
    """
    import mail_client_service.test
