from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(app_module.activities))
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_get_activities_returns_catalog(client):
    # Arrange
    expected_activities = app_module.activities

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Basketball Club"
    email = "student@example.com"
    activity_path = quote(activity_name, safe="")

    # Act
    response = client.post(
        f"/activities/{activity_path}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in app_module.activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Basketball Club"
    email = "student@example.com"
    app_module.activities[activity_name]["participants"].append(email)
    activity_path = quote(activity_name, safe="")

    # Act
    response = client.post(
        f"/activities/{activity_path}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student is already signed up for this activity"}
    assert app_module.activities[activity_name]["participants"].count(email) == 1


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": "student@example.com"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant(client):
    # Arrange
    activity_name = "Basketball Club"
    email = "student@example.com"
    app_module.activities[activity_name]["participants"].append(email)
    activity_path = quote(activity_name, safe="")

    # Act
    response = client.delete(
        f"/activities/{activity_path}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in app_module.activities[activity_name]["participants"]


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/participants",
        params={"email": "student@example.com"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_nonparticipant(client):
    # Arrange
    activity_name = "Basketball Club"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/participants",
        params={"email": "student@example.com"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
