"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_200(self):
        """Test that get activities returns status code 200"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self):
        """Test that get activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)
    
    def test_get_activities_contains_expected_activities(self):
        """Test that get activities contains the expected activity names"""
        response = client.get("/activities")
        activities = response.json()
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Soccer Club",
            "Art Club",
            "Drama Club",
            "Debate Team",
            "Science Club"
        ]
        for activity in expected_activities:
            assert activity in activities
    
    def test_get_activities_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_activity_returns_200(self):
        """Test that signing up returns status code 200"""
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 200
    
    def test_signup_for_activity_returns_success_message(self):
        """Test that signup returns a success message"""
        response = client.post(
            "/activities/Programming%20Class/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "Signed up" in result["message"]
    
    def test_signup_for_nonexistent_activity_returns_404(self):
        """Test that signing up for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_duplicate_student_returns_400(self):
        """Test that signing up a duplicate student returns 400"""
        activity = "Chess Club"
        email = "michael@mergington.edu"  # Already a participant
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_adds_participant_to_activity(self):
        """Test that signup actually adds the participant"""
        activity = "Art Club"
        email = "test.participant@mergington.edu"
        
        # Get initial participant count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify participant was added
        response = client.get("/activities")
        new_count = len(response.json()[activity]["participants"])
        assert new_count == initial_count + 1
        assert email in response.json()[activity]["participants"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""
    
    def test_remove_participant_returns_200(self):
        """Test that removing a participant returns status code 200"""
        # First sign up
        client.post(
            "/activities/Drama%20Club/signup",
            params={"email": "drama.student@mergington.edu"}
        )
        
        # Then remove
        response = client.delete(
            "/activities/Drama%20Club/participants/drama.student%40mergington.edu"
        )
        assert response.status_code == 200
    
    def test_remove_participant_returns_success_message(self):
        """Test that remove returns a success message"""
        # First sign up
        email = "removal.test@mergington.edu"
        client.post(
            "/activities/Debate%20Team/signup",
            params={"email": email}
        )
        
        # Then remove
        response = client.delete(
            f"/activities/Debate%20Team/participants/{email.replace('@', '%40')}"
        )
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "Unregistered" in result["message"]
    
    def test_remove_nonexistent_activity_returns_404(self):
        """Test that removing from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent%20Activity/participants/test%40mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_remove_nonexistent_participant_returns_404(self):
        """Test that removing non-existent participant returns 404"""
        response = client.delete(
            "/activities/Science%20Club/participants/notreal%40mergington.edu"
        )
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]
    
    def test_remove_participant_actually_removes(self):
        """Test that remove actually removes the participant"""
        activity = "Soccer Club"
        email = "soccer.participant@mergington.edu"
        
        # Sign up
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Verify signup worked
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Remove
        client.delete(
            f"/activities/{activity}/participants/{email.replace('@', '%40')}"
        )
        
        # Verify removal
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]


class TestRootEndpoint:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_static_index(self):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
