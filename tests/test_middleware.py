"""
Comprehensive tests for AnonRoleMiddleware focusing on request/response behavior
"""

from unittest.mock import Mock

from django.contrib.auth.models import Group, User
from django.http import HttpResponse
from django.test import RequestFactory, override_settings

import pytest

from django_postgres_anon.middleware import AnonRoleMiddleware


@pytest.fixture
def request_factory():
    """Request factory for creating mock requests"""
    return RequestFactory()


@pytest.fixture
def mock_get_response():
    """Mock get_response function"""
    return Mock(return_value=HttpResponse("Test response"))


@pytest.fixture
@pytest.mark.django_db
def user_with_masked_group():
    """Create user with view_masked_data group"""
    user = User.objects.create_user(username="masked_user", password="test123")
    group, _ = Group.objects.get_or_create(name="view_masked_data")
    user.groups.add(group)
    return user


@pytest.fixture
@pytest.mark.django_db
def user_without_masked_group():
    """Create user without view_masked_data group"""
    return User.objects.create_user(username="normal_user", password="test123")


# Test middleware initialization
def test_middleware_initialization(mock_get_response):
    """Test middleware initializes correctly"""
    middleware = AnonRoleMiddleware(mock_get_response)
    assert middleware.get_response == mock_get_response


# Test middleware request processing behavior
@pytest.mark.django_db
@override_settings(POSTGRES_ANON={"ENABLED": True})
def test_middleware_processes_authenticated_user_with_masked_group(
    request_factory, mock_get_response, user_with_masked_group
):
    """Test middleware handles user with masked data permissions"""
    middleware = AnonRoleMiddleware(mock_get_response)
    request = request_factory.get("/")
    request.user = user_with_masked_group

    response = middleware(request)

    # Should process request and return response
    assert response.status_code == 200
    assert response.content == b"Test response"
    mock_get_response.assert_called_once_with(request)


@pytest.mark.django_db
@override_settings(POSTGRES_ANON={"ENABLED": True})
def test_middleware_processes_authenticated_user_without_masked_group(
    request_factory, mock_get_response, user_without_masked_group
):
    """Test middleware handles user without masked data permissions"""
    middleware = AnonRoleMiddleware(mock_get_response)
    request = request_factory.get("/")
    request.user = user_without_masked_group

    response = middleware(request)

    # Should process request normally
    assert response.status_code == 200
    assert response.content == b"Test response"
    mock_get_response.assert_called_once_with(request)


@pytest.mark.django_db
@override_settings(POSTGRES_ANON={"ENABLED": False})
def test_middleware_bypasses_when_disabled(request_factory, mock_get_response, user_with_masked_group):
    """Test middleware bypasses processing when ANON_ENABLED=False"""
    middleware = AnonRoleMiddleware(mock_get_response)
    request = request_factory.get("/")
    request.user = user_with_masked_group

    response = middleware(request)

    # Should bypass middleware logic and just call get_response
    assert response.status_code == 200
    mock_get_response.assert_called_once_with(request)


@pytest.mark.django_db
def test_middleware_handles_anonymous_user(request_factory, mock_get_response):
    """Test middleware handles anonymous users properly"""
    from django.contrib.auth.models import AnonymousUser

    middleware = AnonRoleMiddleware(mock_get_response)
    request = request_factory.get("/")
    request.user = AnonymousUser()

    response = middleware(request)

    # Should process anonymous users without error
    assert response.status_code == 200
    mock_get_response.assert_called_once_with(request)


@pytest.mark.django_db
def test_middleware_handles_request_without_user(request_factory, mock_get_response):
    """Test middleware handles requests without user attribute"""
    middleware = AnonRoleMiddleware(mock_get_response)
    request = request_factory.get("/")
    # Don't set request.user

    response = middleware(request)

    # Should handle missing user gracefully
    assert response.status_code == 200
    mock_get_response.assert_called_once_with(request)


# Test middleware error handling behavior
@pytest.mark.django_db
def test_middleware_handles_get_response_exception(request_factory, user_with_masked_group):
    """Test middleware handles exceptions from get_response"""

    def failing_get_response(request):
        raise ValueError("Test exception")

    middleware = AnonRoleMiddleware(failing_get_response)
    request = request_factory.get("/")
    request.user = user_with_masked_group

    # Exception should propagate
    with pytest.raises(ValueError, match="Test exception"):
        middleware(request)


@pytest.mark.django_db
def test_middleware_handles_user_group_lookup_error(request_factory, mock_get_response):
    """Test middleware handles errors in user group lookup"""
    # Create a user but delete it after creating the request
    user = User.objects.create_user(username="temp_user", password="test123")
    request = request_factory.get("/")
    request.user = user

    # Delete user to simulate database error
    user.delete()

    middleware = AnonRoleMiddleware(mock_get_response)

    # Should handle the error gracefully
    response = middleware(request)
    assert response.status_code == 200


# Test complete request/response flow
@pytest.mark.django_db
def test_middleware_preserves_request_attributes(request_factory, mock_get_response, user_with_masked_group):
    """Test middleware preserves all request attributes"""
    middleware = AnonRoleMiddleware(mock_get_response)
    request = request_factory.get("/test-path/")
    request.user = user_with_masked_group
    request.session = {}
    request.custom_attr = "test_value"

    middleware(request)

    # Request should be passed through with all attributes preserved
    called_request = mock_get_response.call_args[0][0]
    assert called_request.path == "/test-path/"
    assert called_request.user == user_with_masked_group
    assert hasattr(called_request, "session")
    assert called_request.custom_attr == "test_value"


@pytest.mark.django_db
def test_middleware_returns_unmodified_response(request_factory, user_with_masked_group):
    """Test middleware returns response unmodified"""

    def custom_get_response(request):
        response = HttpResponse("Custom content")
        response["Custom-Header"] = "custom-value"
        response.status_code = 201
        return response

    middleware = AnonRoleMiddleware(custom_get_response)
    request = request_factory.get("/")
    request.user = user_with_masked_group

    response = middleware(request)

    # Response should be returned unmodified
    assert response.status_code == 201
    assert response.content == b"Custom content"
    assert response["Custom-Header"] == "custom-value"


# Test middleware performance characteristics
@pytest.mark.django_db
def test_middleware_minimal_database_queries(request_factory, mock_get_response, user_with_masked_group):
    """Test middleware doesn't make excessive database queries"""
    from django.db import connection

    middleware = AnonRoleMiddleware(mock_get_response)
    request = request_factory.get("/")
    request.user = user_with_masked_group

    # Reset query count
    connection.queries_log.clear()
    initial_queries = len(connection.queries)

    middleware(request)

    # Should not make excessive queries
    query_count = len(connection.queries) - initial_queries
    assert query_count <= 5  # Allow some reasonable number of queries


@pytest.mark.django_db
def test_middleware_handles_multiple_requests(request_factory, mock_get_response, user_with_masked_group):
    """Test middleware handles multiple consecutive requests"""
    middleware = AnonRoleMiddleware(mock_get_response)

    # Process multiple requests
    for i in range(5):
        request = request_factory.get(f"/page-{i}/")
        request.user = user_with_masked_group
        response = middleware(request)
        assert response.status_code == 200

    # Should handle all requests successfully
    assert mock_get_response.call_count == 5


# Test edge cases and boundary conditions
@pytest.mark.django_db
def test_middleware_with_user_in_multiple_groups(request_factory, mock_get_response):
    """Test middleware with user in multiple groups including masked group"""
    user = User.objects.create_user(username="multi_group_user", password="test123")
    group1, _ = Group.objects.get_or_create(name="view_masked_data")
    group2, _ = Group.objects.get_or_create(name="other_group")
    user.groups.add(group1, group2)

    middleware = AnonRoleMiddleware(mock_get_response)
    request = request_factory.get("/")
    request.user = user

    response = middleware(request)

    # Should handle user with multiple groups
    assert response.status_code == 200
    mock_get_response.assert_called_once_with(request)


@pytest.mark.django_db
def test_middleware_with_superuser(request_factory, mock_get_response):
    """Test middleware behavior with superuser"""
    user = User.objects.create_superuser(username="admin", password="test123", email="admin@test.com")

    middleware = AnonRoleMiddleware(mock_get_response)
    request = request_factory.get("/")
    request.user = user

    response = middleware(request)

    # Should handle superuser normally
    assert response.status_code == 200
    mock_get_response.assert_called_once_with(request)


@pytest.mark.django_db
def test_middleware_with_staff_user(request_factory, mock_get_response):
    """Test middleware behavior with staff user"""
    user = User.objects.create_user(username="staff", password="test123", is_staff=True)

    middleware = AnonRoleMiddleware(mock_get_response)
    request = request_factory.get("/")
    request.user = user

    response = middleware(request)

    # Should handle staff user normally
    assert response.status_code == 200
    mock_get_response.assert_called_once_with(request)
