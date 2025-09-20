import logging
from typing import Callable

from django.db import connection
from django.http import HttpRequest, HttpResponse

from django_postgres_anon.config import anon_config
from django_postgres_anon.utils import reset_role, switch_to_role

logger = logging.getLogger(__name__)


class AnonRoleMiddleware:
    """
    Middleware for dynamic role switching based on user permissions.

    Users in the ANON_MASKED_GROUP will see anonymized data automatically.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        used_mask = False

        try:
            should_mask = (
                anon_config.enabled
                and request.user.is_authenticated
                and request.user.groups.filter(name=anon_config.masked_group).exists()
            )

            if should_mask:
                masked_role = anon_config.default_masked_role

                if switch_to_role(masked_role, auto_create=True):
                    used_mask = True
                    # Set search path for anonymization
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute("SET search_path = mask, public")
                        logger.debug(f"Switched to masked role for user: {request.user.username}")
                    except Exception as e:
                        logger.warning(f"Failed to set search_path: {e}")
                else:
                    logger.error(f"Failed to switch to masked role {masked_role}")
                    # Continue without masking

            response = self.get_response(request)
            return response

        except Exception as e:
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
                    except Exception as e:
                        logger.error(f"Failed to reset search_path: {e}")
                else:
                    logger.error("Failed to reset database role")
