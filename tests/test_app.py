from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def signup_url(activity_name):
    return f"/activities/{quote(activity_name, safe='')}/signup"


def test_get_activities_returns_activity_details(client):
    # Arrange
    expected_activity = activities["Chess Club"]

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()["Chess Club"] == expected_activity
    assert response.json()["Soccer Team"]["participants"] == []


def test_signup_adds_normalized_email(client):
    # Arrange
    activity_name = "Soccer Team"
    email = "  STUDENT@mergington.edu "

    # Act
    response = client.post(
        signup_url(activity_name),
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert "student@mergington.edu" in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_email_case_insensitively(client):
    # Arrange
    activity_name = "Chess Club"
    email = "  MICHAEL@mergington.edu "

    # Act
    response = client.post(
        signup_url(activity_name),
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        signup_url(activity_name),
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_email_case_insensitively(client):
    # Arrange
    activity_name = "Chess Club"
    email = "  MICHAEL@mergington.edu "

    # Act
    response = client.delete(
        signup_url(activity_name),
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert "michael@mergington.edu" not in activities[activity_name]["participants"]


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        signup_url(activity_name),
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_non_participant(client):
    # Arrange
    activity_name = "Soccer Team"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        signup_url(activity_name),
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
