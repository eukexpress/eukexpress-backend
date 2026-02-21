# Eukexpress\backend\tests\test_auth.py
"""
Authentication Tests
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_success():
    """Test successful login"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "EukExpress@2024Admin"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_failure():
    """Test failed login"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "wrongpassword"}
    )
    assert response.status_code == 401

def test_verify_token():
    """Test token verification"""
    # First login to get token
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "EukExpress@2024Admin"}
    )
    token = login_response.json()["access_token"]
    
    # Verify token
    response = client.get(
        "/api/v1/auth/verify",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["valid"] == True