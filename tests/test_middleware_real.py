"""
Tests for AnonRoleMiddleware using real PostgreSQL database operations

These tests use the actual PostgreSQL database and anon extension
to verify middleware behavior with real database role switching.
"""

from unittest.mock import Mock

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.http import HttpResponse
from django.test import RequestFactory, override_settings

import pytest

from django_postgres_anon.middleware import AnonRoleMiddleware


@pytest.fixture
def request_factory():
    """Request factory for creating mock requests"""
    return RequestFactory()


@pytest.fixture
def simple_get_response():
    """Simple get_response function that returns 200"""

    def get_response(request):
        return HttpResponse("Test response", status=200)

    return get_response


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


@pytest.fixture
def initialized_extension():
    """Ensure anon extension is initialized"""
    try:
        call_command("anon_init", "--force")
        yield
    except CommandError as e:
        if "extension" in str(e).lower():
            pytest.skip(f"PostgreSQL anon extension not available: {e}")
        raise


class TestMiddlewareWithRealDatabase:
    """Test middleware with real PostgreSQL database operations"""

    @pytest.mark.django_db(transaction=True)
    @override_settings(
        POSTGRES_ANON={"ENABLED": True, "MASKED_GROUP": "view_masked_data", "DEFAULT_MASKED_ROLE": "test_masked_reader"}
    )
    def test_middleware_processes_request_with_real_db(
        self, initialized_extension, request_factory, simple_get_response, user_with_masked_group
    ):
        """Test middleware processes requests using real database"""
        middleware = AnonRoleMiddleware(simple_get_response)
        request = request_factory.get("/")
        request.user = user_with_masked_group

        # This uses the real database and anon extension
        response = middleware(request)

        # Should complete successfully whether role switching succeeds or fails
        assert response.status_code == 200
        assert response.content == b"Test response"

    @pytest.mark.django_db(transaction=True)
    @override_settings(
        POSTGRES_ANON={"ENABLED": True, "MASKED_GROUP": "view_masked_data", "DEFAULT_MASKED_ROLE": "test_masked_reader"}
    )
    def test_middleware_with_user_without_group(
        self, initialized_extension, request_factory, simple_get_response, user_without_masked_group
    ):
        """Test middleware with user not in masked group"""
        middleware = AnonRoleMiddleware(simple_get_response)
        request = request_factory.get("/")
        request.user = user_without_masked_group

        response = middleware(request)

        # Should process normally without role switching
        assert response.status_code == 200
        assert response.content == b"Test response"

    @pytest.mark.django_db(transaction=True)
    @override_settings(
        POSTGRES_ANON={
            "ENABLED": False,
            "MASKED_GROUP": "view_masked_data",
            "DEFAULT_MASKED_ROLE": "test_masked_reader",
        }
    )
    def test_middleware_when_disabled(
        self, initialized_extension, request_factory, simple_get_response, user_with_masked_group
    ):
        """Test middleware when anonymization is disabled"""
        middleware = AnonRoleMiddleware(simple_get_response)
        request = request_factory.get("/")
        request.user = user_with_masked_group

        response = middleware(request)

        # Should process normally when disabled
        assert response.status_code == 200
        assert response.content == b"Test response"

    @pytest.mark.django_db(transaction=True)
    def test_middleware_with_anonymous_user(self, initialized_extension, request_factory, simple_get_response):
        """Test middleware with anonymous user"""
        from django.contrib.auth.models import AnonymousUser

        middleware = AnonRoleMiddleware(simple_get_response)
        request = request_factory.get("/")
        request.user = AnonymousUser()

        response = middleware(request)

        # Should process anonymous users without issues
        assert response.status_code == 200
        assert response.content == b"Test response"

    @pytest.mark.django_db(transaction=True)
    @override_settings(
        POSTGRES_ANON={"ENABLED": True, "MASKED_GROUP": "view_masked_data", "DEFAULT_MASKED_ROLE": "test_masked_reader"}
    )
    def test_middleware_handles_database_errors_gracefully(
        self, request_factory, simple_get_response, user_with_masked_group
    ):
        """Test middleware handles database connection errors gracefully"""
        # Even without initialized extension, middleware should not crash
        middleware = AnonRoleMiddleware(simple_get_response)
        request = request_factory.get("/")
        request.user = user_with_masked_group

        response = middleware(request)

        # Should handle database errors gracefully and continue processing
        assert response.status_code == 200
        assert response.content == b"Test response"

    @pytest.mark.django_db(transaction=True)
    @override_settings(
        POSTGRES_ANON={"ENABLED": True, "MASKED_GROUP": "view_masked_data", "DEFAULT_MASKED_ROLE": "test_masked_reader"}
    )
    def test_middleware_with_get_response_exception(
        self, initialized_extension, request_factory, user_with_masked_group
    ):
        """Test middleware when get_response raises exception"""

        def failing_get_response(_request):
            raise ValueError("View processing error")

        middleware = AnonRoleMiddleware(failing_get_response)
        request = request_factory.get("/")
        request.user = user_with_masked_group

        # Exception should be propagated after middleware cleanup
        with pytest.raises(ValueError, match="View processing error"):
            middleware(request)

    @pytest.mark.django_db(transaction=True)
    @override_settings(
        POSTGRES_ANON={"ENABLED": True, "MASKED_GROUP": "view_masked_data", "DEFAULT_MASKED_ROLE": "test_masked_reader"}
    )
    def test_middleware_preserves_request_attributes(
        self, initialized_extension, request_factory, user_with_masked_group
    ):
        """Test middleware preserves all request attributes"""

        def capturing_get_response(request):
            # Verify request attributes are preserved
            assert hasattr(request, "user")
            assert hasattr(request, "path")
            assert hasattr(request, "method")
            assert request.custom_attr == "test_value"
            return HttpResponse("Captured request", status=200)

        middleware = AnonRoleMiddleware(capturing_get_response)
        request = request_factory.get("/test-path/")
        request.user = user_with_masked_group
        request.custom_attr = "test_value"

        response = middleware(request)

        assert response.status_code == 200
        assert response.content == b"Captured request"

    @pytest.mark.django_db(transaction=True)
    @override_settings(
        POSTGRES_ANON={"ENABLED": True, "MASKED_GROUP": "view_masked_data", "DEFAULT_MASKED_ROLE": "test_masked_reader"}
    )
    def test_middleware_with_multiple_requests(
        self, initialized_extension, request_factory, simple_get_response, user_with_masked_group
    ):
        """Test middleware handles multiple consecutive requests"""
        middleware = AnonRoleMiddleware(simple_get_response)

        # Process multiple requests
        for i in range(3):
            request = request_factory.get(f"/page-{i}/")
            request.user = user_with_masked_group

            response = middleware(request)

            assert response.status_code == 200
            assert response.content == b"Test response"

    @pytest.mark.django_db(transaction=True)
    @override_settings(
        POSTGRES_ANON={"ENABLED": True, "MASKED_GROUP": "view_masked_data", "DEFAULT_MASKED_ROLE": "test_masked_reader"}
    )
    def test_middleware_with_custom_response(self, initialized_extension, request_factory, user_with_masked_group):
        """Test middleware returns custom response unchanged"""

        def custom_get_response(_request):
            response = HttpResponse("Custom response content", status=201)
            response["Custom-Header"] = "custom-value"
            return response

        middleware = AnonRoleMiddleware(custom_get_response)
        request = request_factory.get("/")
        request.user = user_with_masked_group

        response = middleware(request)

        # Response should be returned unchanged
        assert response.status_code == 201
        assert response.content == b"Custom response content"
        assert response["Custom-Header"] == "custom-value"

    @pytest.mark.django_db(transaction=True)
    def test_middleware_without_anon_extension(self, request_factory, simple_get_response, user_with_masked_group):
        """Test middleware behavior when anon extension is not available"""
        # Don't use initialized_extension fixture - test without extension
        middleware = AnonRoleMiddleware(simple_get_response)
        request = request_factory.get("/")
        request.user = user_with_masked_group

        response = middleware(request)

        # Should handle missing extension gracefully
        assert response.status_code == 200
        assert response.content == b"Test response"


class TestMiddlewareErrorHandling:
    """Test middleware error handling with real database scenarios"""

    @pytest.mark.django_db(transaction=True)
    @override_settings(
        POSTGRES_ANON={"ENABLED": True, "MASKED_GROUP": "view_masked_data", "DEFAULT_MASKED_ROLE": "test_masked_reader"}
    )
    def test_middleware_handles_user_group_errors(self, request_factory, simple_get_response):
        """Test middleware handles user group access errors"""
        middleware = AnonRoleMiddleware(simple_get_response)
        request = request_factory.get("/")

        # Create a mock user that will cause an error when accessing groups
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.groups.filter.side_effect = Exception("Group access error")
        request.user = mock_user

        response = middleware(request)

        # Should handle error gracefully
        assert response.status_code == 200
        assert response.content == b"Test response"

    @pytest.mark.django_db(transaction=True)
    def test_middleware_handles_missing_user_attribute(self, request_factory, simple_get_response):
        """Test middleware handles requests without user attribute"""
        middleware = AnonRoleMiddleware(simple_get_response)
        request = request_factory.get("/")
        # Don't set request.user

        response = middleware(request)

        # Should handle missing user gracefully
        assert response.status_code == 200
        assert response.content == b"Test response"

    @pytest.mark.django_db(transaction=True)
    @override_settings(
        POSTGRES_ANON={"ENABLED": True, "MASKED_GROUP": "view_masked_data", "DEFAULT_MASKED_ROLE": "test_masked_reader"}
    )
    def test_middleware_performance_with_real_db(
        self, initialized_extension, request_factory, simple_get_response, user_with_masked_group
    ):
        """Test middleware performance doesn't degrade with real database"""
        middleware = AnonRoleMiddleware(simple_get_response)
        request = request_factory.get("/")
        request.user = user_with_masked_group

        # Process request multiple times to ensure no performance degradation
        import time

        start_time = time.time()

        for _ in range(5):
            response = middleware(request)
            assert response.status_code == 200

        end_time = time.time()

        # Should complete reasonably quickly (less than 5 seconds for 5 requests)
        assert (end_time - start_time) < 5.0

    @pytest.mark.django_db(transaction=True)
    @override_settings(
        POSTGRES_ANON={"ENABLED": True, "MASKED_GROUP": "view_masked_data", "DEFAULT_MASKED_ROLE": "test_masked_reader"}
    )
    def test_middleware_with_different_user_types(self, initialized_extension, request_factory, simple_get_response):
        """Test middleware with different types of users"""
        middleware = AnonRoleMiddleware(simple_get_response)

        # Test with superuser
        superuser = User.objects.create_superuser(username="admin", password="test123", email="admin@test.com")
        request = request_factory.get("/")
        request.user = superuser
        response = middleware(request)
        assert response.status_code == 200

        # Test with staff user
        staff_user = User.objects.create_user(username="staff", password="test123", is_staff=True)
        request = request_factory.get("/")
        request.user = staff_user
        response = middleware(request)
        assert response.status_code == 200

        # Test with user in multiple groups
        multi_group_user = User.objects.create_user(username="multi", password="test123")
        group1, _ = Group.objects.get_or_create(name="view_masked_data")
        group2, _ = Group.objects.get_or_create(name="other_group")
        multi_group_user.groups.add(group1, group2)

        request = request_factory.get("/")
        request.user = multi_group_user
        response = middleware(request)
        assert response.status_code == 200


class TestMiddlewareIntegration:
    """Test middleware integration with other components"""

    @pytest.mark.django_db(transaction=True)
    @override_settings(
        POSTGRES_ANON={"ENABLED": True, "MASKED_GROUP": "view_masked_data", "DEFAULT_MASKED_ROLE": "test_masked_reader"}
    )
    def test_middleware_with_session_data(
        self, initialized_extension, request_factory, simple_get_response, user_with_masked_group
    ):
        """Test middleware preserves session data"""

        def session_checking_response(request):
            # Verify session is accessible
            request.session["test_key"] = "test_value"
            return HttpResponse(f"Session data: {request.session.get('test_key', 'missing')}")

        middleware = AnonRoleMiddleware(session_checking_response)
        request = request_factory.get("/")
        request.user = user_with_masked_group

        # Add session middleware functionality
        from django.contrib.sessions.middleware import SessionMiddleware

        session_middleware = SessionMiddleware(lambda r: None)
        session_middleware.process_request(request)

        response = middleware(request)

        assert response.status_code == 200
        assert b"Session data: test_value" in response.content

    @pytest.mark.django_db(transaction=True)
    def test_middleware_initialization(self, simple_get_response):
        """Test middleware initializes correctly"""
        middleware = AnonRoleMiddleware(simple_get_response)
        assert middleware.get_response == simple_get_response
        assert callable(middleware)

    @pytest.mark.django_db(transaction=True)
    @override_settings(
        POSTGRES_ANON={"ENABLED": True, "MASKED_GROUP": "view_masked_data", "DEFAULT_MASKED_ROLE": "test_masked_reader"}
    )
    def test_middleware_thread_safety(
        self, initialized_extension, request_factory, simple_get_response, user_with_masked_group
    ):
        """Test middleware is thread-safe"""
        import queue
        import threading

        middleware = AnonRoleMiddleware(simple_get_response)
        results = queue.Queue()

        def process_request():
            request = request_factory.get("/")
            request.user = user_with_masked_group
            response = middleware(request)
            results.put(response.status_code)

        # Create multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=process_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all requests processed successfully
        status_codes = []
        while not results.empty():
            status_codes.append(results.get())

        assert len(status_codes) == 3
        assert all(status == 200 for status in status_codes)
