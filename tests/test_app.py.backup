
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.app import app, accounts, transactions


def setup_function():
    accounts["1001"]["balance"] = 50000.00
    accounts["1002"]["balance"] = 25000.00
    transactions.clear()


def test_homepage():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"SecureBank" in response.data


def test_health():
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "UP"


def test_successful_transfer():
    client = app.test_client()

    response = client.post(
        "/transfer",
        data={
            "sender": "1001",
            "receiver": "1002",
            "amount": "1000"
        }
    )

    assert response.status_code == 302
    assert accounts["1001"]["balance"] == 49000.00
    assert accounts["1002"]["balance"] == 26000.00


def test_insufficient_balance():
    client = app.test_client()

    client.post(
        "/transfer",
        data={
            "sender": "1001",
            "receiver": "1002",
            "amount": "100000"
        }
    )

    assert accounts["1001"]["balance"] == 50000.00
    assert accounts["1002"]["balance"] == 25000.00


def test_same_account_transfer():
    client = app.test_client()

    client.post(
        "/transfer",
        data={
            "sender": "1001",
            "receiver": "1001",
            "amount": "500"
        }
    )

    assert accounts["1001"]["balance"] == 50000.00
