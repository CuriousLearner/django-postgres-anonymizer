import logging
from typing import Callable

from django.db import DatabaseError, OperationalError, connection
from django.http import HttpRequest, HttpResponse

from django_postgres_anon.config import get_anon_setting
from django_postgres_anon.utils import reset_role, switch_to_role

logger = logging.getLogger(__name__)


class AnonRoleMiddleware:
    """
    Middleware for dynamic role switching based on user permissions.

    Users in any of the ANON_MASKED_GROUPS will see anonymized data automatically.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        used_mask = False

        try:
            # Check if user should have data masked - defensive against user access issues
            try:
                masked_groups = get_anon_setting("MASKED_GROUPS")
                should_mask = (
                    get_anon_setting("ENABLED")
                    and request.user.is_authenticated
                    and request.user.groups.filter(name__in=masked_groups).exists()
                )
            except Exception:
                # If there's any issue with user/group access, default to no masking
                should_mask = False

            if should_mask:
                masked_role = get_anon_setting("DEFAULT_MASKED_ROLE")

                if switch_to_role(masked_role, auto_create=True):
                    used_mask = True
                    # Set search path for anonymization
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("SET search_path = mask, public")
                        logger.debug(f"Switched to masked role for user: {request.user.username}")
                    except (DatabaseError, OperationalError) as e:
                        logger.warning(f"Failed to set search_path: {e}")
                else:
                    logger.error(f"Failed to switch to masked role {masked_role}")
                    # Continue without masking

            response = self.get_response(request)
            return response

        except (DatabaseError, OperationalError) as e:
            logger.error(f"Error in AnonRoleMiddleware: {e}")
            # Continue without masking on error
            return self.get_response(request)

        finally:
            if used_mask:
                # Critical: Reset role for connection pooling
                if reset_role():
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("SET search_path = public")
                        logger.debug("Reset database role and search_path")
                    except (DatabaseError, OperationalError) as e:
                        logger.error(f"Failed to reset search_path: {e}")
                else:
                    logger.error("Failed to reset database role")
