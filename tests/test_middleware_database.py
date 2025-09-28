"""
Tests for AnonRoleMiddleware database role switching functionality
"""

from unittest.mock import Mock, patch

import pytest
from django.contrib.auth.models import Group, User
from django.db import DatabaseError, OperationalError
from django.http import HttpResponse
from django.test import RequestFactory

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


class TestMiddlewareRoleSwitching:
    """Test actual database role switching functionality"""

    @pytest.mark.django_db(transaction=True)
    def test_middleware_switches_to_masked_role_successfully(
        self, request_factory, mock_get_response, user_with_masked_group
    ):
        """Test middleware switches to masked role when conditions are met"""
        middleware = AnonRoleMiddleware(mock_get_response)
        request = request_factory.get("/")
        request.user = user_with_masked_group

        with patch("django_postgres_anon.middleware.switch_to_role") as mock_switch:
            with patch("django_postgres_anon.middleware.reset_role") as mock_reset:
                with patch("django_postgres_anon.middleware.get_anon_setting") as mock_get_setting:

                    def mock_setting(key):
                        settings_map = {
                            "ENABLED": True,
                            "MASKED_GROUP": "view_masked_data",
                            "DEFAULT_MASKED_ROLE": "masked_reader",
                        }
                        return settings_map.get(key)

                    mock_get_setting.side_effect = mock_setting
                    mock_switch.return_value = True
                    mock_reset.return_value = True

                    response = middleware(request)

                    mock_switch.assert_called_once_with("masked_reader", auto_create=True)
                    mock_reset.assert_called_once()
                    assert response.status_code == 200

    @pytest.mark.django_db(transaction=True)
    def test_middleware_handles_role_switch_failure(self, request_factory, mock_get_response, user_with_masked_group):
        """Test middleware handles role switching failure gracefully"""
        middleware = AnonRoleMiddleware(mock_get_response)
        request = request_factory.get("/")
        request.user = user_with_masked_group

        with patch("django_postgres_anon.middleware.switch_to_role") as mock_switch:
            with patch("django_postgres_anon.middleware.reset_role") as mock_reset:
                with patch("django_postgres_anon.middleware.get_anon_setting") as mock_get_setting:

                    def mock_setting(key):
                        settings_map = {
                            "ENABLED": True,
                            "MASKED_GROUP": "view_masked_data",
                            "DEFAULT_MASKED_ROLE": "masked_reader",
                        }
                        return settings_map.get(key)

                    mock_get_setting.side_effect = mock_setting
                    mock_switch.return_value = False

                    response = middleware(request)

                    mock_switch.assert_called_once_with("masked_reader", auto_create=True)
                    mock_reset.assert_not_called()
                    assert response.status_code == 200

    @pytest.mark.django_db(transaction=True)
    def test_middleware_sets_search_path_after_role_switch(
        self, request_factory, mock_get_response, user_with_masked_group
    ):
        """Test middleware sets search_path after successful role switch"""
        middleware = AnonRoleMiddleware(mock_get_response)
        request = request_factory.get("/")
        request.user = user_with_masked_group

        with patch("django_postgres_anon.middleware.switch_to_role") as mock_switch:
            with patch("django_postgres_anon.middleware.reset_role") as mock_reset:
                with patch("django.db.connection.cursor") as mock_cursor:
                    with patch("django_postgres_anon.middleware.get_anon_setting") as mock_get_setting:
                        cursor_mock = Mock()
                        mock_cursor.return_value.__enter__.return_value = cursor_mock

                        def mock_setting(key):
                            settings_map = {
                                "ENABLED": True,
                                "MASKED_GROUP": "view_masked_data",
                                "DEFAULT_MASKED_ROLE": "masked_reader",
                            }
                            return settings_map.get(key)

                        mock_get_setting.side_effect = mock_setting
                        mock_switch.return_value = True
                        mock_reset.return_value = True

                        response = middleware(request)

                        cursor_mock.execute.assert_any_call("SET search_path = mask, public")
                        assert response.status_code == 200

    @pytest.mark.django_db(transaction=True)
    def test_middleware_handles_search_path_error(self, request_factory, mock_get_response, user_with_masked_group):
        """Test middleware handles search_path setting errors"""
        middleware = AnonRoleMiddleware(mock_get_response)
        request = request_factory.get("/")
        request.user = user_with_masked_group

        with patch("django_postgres_anon.middleware.switch_to_role") as mock_switch:
            with patch("django_postgres_anon.middleware.reset_role") as mock_reset:
                with patch("django.db.connection.cursor") as mock_cursor:
                    with patch("django_postgres_anon.middleware.get_anon_setting") as mock_get_setting:
                        cursor_mock = Mock()
                        cursor_mock.execute.side_effect = DatabaseError("Search path error")
                        mock_cursor.return_value.__enter__.return_value = cursor_mock

                        def mock_setting(key):
                            settings_map = {
                                "ENABLED": True,
                                "MASKED_GROUP": "view_masked_data",
                                "DEFAULT_MASKED_ROLE": "masked_reader",
                            }
                            return settings_map.get(key)

                        mock_get_setting.side_effect = mock_setting
                        mock_switch.return_value = True
                        mock_reset.return_value = True

                        response = middleware(request)

                        assert response.status_code == 200
                        mock_reset.assert_called_once()

    @pytest.mark.django_db(transaction=True)
    def test_middleware_resets_role_in_finally_block(self, request_factory, mock_get_response, user_with_masked_group):
        """Test middleware always resets role in finally block"""
        middleware = AnonRoleMiddleware(mock_get_response)
        request = request_factory.get("/")
        request.user = user_with_masked_group

        with patch("django_postgres_anon.middleware.switch_to_role") as mock_switch:
            with patch("django_postgres_anon.middleware.reset_role") as mock_reset:
                with patch("django.db.connection.cursor") as mock_cursor:
                    with patch("django_postgres_anon.middleware.get_anon_setting") as mock_get_setting:
                        cursor_mock = Mock()
                        mock_cursor.return_value.__enter__.return_value = cursor_mock

                        def mock_setting(key):
                            settings_map = {
                                "ENABLED": True,
                                "MASKED_GROUP": "view_masked_data",
                                "DEFAULT_MASKED_ROLE": "masked_reader",
                            }
                            return settings_map.get(key)

                        mock_get_setting.side_effect = mock_setting
                        mock_switch.return_value = True
                        mock_reset.return_value = True

                        response = middleware(request)

                        mock_reset.assert_called_once()
                        cursor_mock.execute.assert_any_call("SET search_path = public")
                        assert response.status_code == 200

    @pytest.mark.django_db(transaction=True)
    def test_middleware_handles_role_reset_failure(self, request_factory, mock_get_response, user_with_masked_group):
        """Test middleware handles role reset failure"""
        middleware = AnonRoleMiddleware(mock_get_response)
        request = request_factory.get("/")
        request.user = user_with_masked_group

        with patch("django_postgres_anon.middleware.switch_to_role") as mock_switch:
            with patch("django_postgres_anon.middleware.reset_role") as mock_reset:
                with patch("django_postgres_anon.middleware.get_anon_setting") as mock_get_setting:

                    def mock_setting(key):
                        settings_map = {
                            "ENABLED": True,
                            "MASKED_GROUP": "view_masked_data",
                            "DEFAULT_MASKED_ROLE": "masked_reader",
                        }
                        return settings_map.get(key)

                    mock_get_setting.side_effect = mock_setting
                    mock_switch.return_value = True
                    mock_reset.return_value = False  # Reset fails

                    response = middleware(request)

                    assert response.status_code == 200
                    mock_reset.assert_called_once()

    @pytest.mark.django_db(transaction=True)
    def test_middleware_handles_search_path_reset_error(
        self, request_factory, mock_get_response, user_with_masked_group
    ):
        """Test middleware handles search_path reset errors"""
        middleware = AnonRoleMiddleware(mock_get_response)
        request = request_factory.get("/")
        request.user = user_with_masked_group

        with patch("django_postgres_anon.middleware.switch_to_role") as mock_switch:
            with patch("django_postgres_anon.middleware.reset_role") as mock_reset:
                with patch("django.db.connection.cursor") as mock_cursor:
                    with patch("django_postgres_anon.middleware.get_anon_setting") as mock_get_setting:
                        cursor_mock = Mock()
                        # First call (set mask path) succeeds, second call (reset path) fails
                        cursor_mock.execute.side_effect = [None, OperationalError("Reset path error")]
                        mock_cursor.return_value.__enter__.return_value = cursor_mock

                        def mock_setting(key):
                            settings_map = {
                                "ENABLED": True,
                                "MASKED_GROUP": "view_masked_data",
                                "DEFAULT_MASKED_ROLE": "masked_reader",
                            }
                            return settings_map.get(key)

                        mock_get_setting.side_effect = mock_setting
                        mock_switch.return_value = True
                        mock_reset.return_value = True

                        response = middleware(request)

                        assert response.status_code == 200

    @pytest.mark.django_db(transaction=True)
    def test_middleware_doesnt_switch_for_user_without_group(
        self, request_factory, mock_get_response, user_without_masked_group
    ):
        """Test middleware doesn't switch roles for users without masked group"""
        middleware = AnonRoleMiddleware(mock_get_response)
        request = request_factory.get("/")
        request.user = user_without_masked_group

        with patch("django_postgres_anon.middleware.switch_to_role") as mock_switch:
            with patch("django_postgres_anon.middleware.reset_role") as mock_reset:
                with patch("django_postgres_anon.middleware.get_anon_setting") as mock_get_setting:

                    def mock_setting(key):
                        settings_map = {
                            "ENABLED": True,
                            "MASKED_GROUP": "view_masked_data",
                            "DEFAULT_MASKED_ROLE": "masked_reader",
                        }
                        return settings_map.get(key)

                    mock_get_setting.side_effect = mock_setting

                    response = middleware(request)

                    mock_switch.assert_not_called()
                    mock_reset.assert_not_called()
                    assert response.status_code == 200

    @pytest.mark.django_db(transaction=True)
    def test_middleware_bypasses_when_disabled(self, request_factory, mock_get_response, user_with_masked_group):
        """Test middleware bypasses role switching when disabled"""
        middleware = AnonRoleMiddleware(mock_get_response)
        request = request_factory.get("/")
        request.user = user_with_masked_group

        with patch("django_postgres_anon.middleware.switch_to_role") as mock_switch:
            with patch("django_postgres_anon.middleware.reset_role") as mock_reset:
                with patch("django_postgres_anon.middleware.get_anon_setting") as mock_get_setting:

                    def mock_setting(key):
                        settings_map = {
                            "ENABLED": False,  # Disabled
                            "MASKED_GROUP": "view_masked_data",
                            "DEFAULT_MASKED_ROLE": "masked_reader",
                        }
                        return settings_map.get(key)

                    mock_get_setting.side_effect = mock_setting

                    response = middleware(request)

                    mock_switch.assert_not_called()
                    mock_reset.assert_not_called()
                    assert response.status_code == 200

    @pytest.mark.django_db(transaction=True)
    def test_middleware_handles_exception_during_processing(self, request_factory, user_with_masked_group):
        """Test middleware handles exceptions during processing"""

        def failing_get_response(_request):
            raise ValueError("Processing error")

        middleware = AnonRoleMiddleware(failing_get_response)
        request = request_factory.get("/")
        request.user = user_with_masked_group

        with patch("django_postgres_anon.middleware.switch_to_role") as mock_switch:
            with patch("django_postgres_anon.middleware.reset_role") as mock_reset:
                with patch("django_postgres_anon.middleware.get_anon_setting") as mock_get_setting:

                    def mock_setting(key):
                        settings_map = {
                            "ENABLED": True,
                            "MASKED_GROUP": "view_masked_data",
                            "DEFAULT_MASKED_ROLE": "masked_reader",
                        }
                        return settings_map.get(key)

                    mock_get_setting.side_effect = mock_setting
                    mock_switch.return_value = True
                    mock_reset.return_value = True

                    # Exception should be caught, logged, and then re-raised
                    with pytest.raises(ValueError, match="Processing error"):
                        middleware(request)

                    # Role should still be reset in finally block even when exception occurs
                    mock_reset.assert_called_once()

    @pytest.mark.django_db(transaction=True)
    def test_middleware_with_custom_masked_role(self, request_factory, mock_get_response, user_with_masked_group):
        """Test middleware uses custom masked role from config"""
        middleware = AnonRoleMiddleware(mock_get_response)
        request = request_factory.get("/")
        request.user = user_with_masked_group

        with patch("django_postgres_anon.middleware.switch_to_role") as mock_switch:
            with patch("django_postgres_anon.middleware.reset_role") as mock_reset:
                with patch("django_postgres_anon.middleware.get_anon_setting") as mock_get_setting:

                    def mock_setting(key):
                        settings_map = {
                            "ENABLED": True,
                            "MASKED_GROUP": "view_masked_data",
                            "DEFAULT_MASKED_ROLE": "custom_masked_role",
                        }
                        return settings_map.get(key)

                    mock_get_setting.side_effect = mock_setting
                    mock_switch.return_value = True
                    mock_reset.return_value = True

                    response = middleware(request)

                    # Should use custom role name
                    mock_switch.assert_called_once_with("custom_masked_role", auto_create=True)
                    assert response.status_code == 200


class TestMiddlewareErrorHandling:
    """Test middleware error handling with actual database scenarios"""

    @pytest.mark.django_db(transaction=True)
    def test_middleware_handles_database_connection_error(
        self, request_factory, mock_get_response, user_with_masked_group
    ):
        """Test middleware handles database connection errors"""
        middleware = AnonRoleMiddleware(mock_get_response)
        request = request_factory.get("/")
        request.user = user_with_masked_group

        with patch("django_postgres_anon.middleware.switch_to_role") as mock_switch:
            with patch("django_postgres_anon.middleware.get_anon_setting") as mock_get_setting:

                def mock_setting(key):
                    settings_map = {
                        "ENABLED": True,
                        "MASKED_GROUP": "view_masked_data",
                        "DEFAULT_MASKED_ROLE": "masked_reader",
                    }
                    return settings_map.get(key)

                mock_get_setting.side_effect = mock_setting
                # Simulate database connection error
                mock_switch.side_effect = DatabaseError("Database connection failed")

                response = middleware(request)

                # Should handle error gracefully and continue processing
                assert response.status_code == 200

    @pytest.mark.django_db(transaction=True)
    def test_middleware_handles_user_group_access_error(self, request_factory, mock_get_response):
        """Test middleware handles user group access errors"""
        middleware = AnonRoleMiddleware(mock_get_response)
        request = request_factory.get("/")

        # Create a mock user that will cause an error when accessing groups
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.groups.filter.side_effect = Exception("Group access error")
        request.user = mock_user

        with patch("django_postgres_anon.middleware.get_anon_setting") as mock_get_setting:

            def mock_setting(key):
                settings_map = {
                    "ENABLED": True,
                    "MASKED_GROUP": "view_masked_data",
                    "DEFAULT_MASKED_ROLE": "masked_reader",
                }
                return settings_map.get(key)

            mock_get_setting.side_effect = mock_setting

            response = middleware(request)

            # Should handle error gracefully
            assert response.status_code == 200
