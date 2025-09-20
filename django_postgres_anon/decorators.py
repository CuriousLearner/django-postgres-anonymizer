"""Decorators for dynamic anonymization role switching"""

import functools
import logging
from typing import Callable, Optional

from django_postgres_anon.context_managers import anonymized_data

logger = logging.getLogger(__name__)


def use_anonymized_data(role_name: Optional[str] = None, auto_create: bool = True):
    """
    Decorator for automatically using anonymized data in views/functions.

    This decorator wraps the function execution in the anonymized_data context manager,
    ensuring all database queries within the function see anonymized data.

    Args:
        role_name: Name of the masked role to use. Defaults to 'masked_reader'.
        auto_create: Whether to automatically create the role if it doesn't exist.

    Example:
        >>> @use_anonymized_data
        >>> def sensitive_report(request):
        ...     users = User.objects.all()  # Returns anonymized user data
        ...     return render(request, 'report.html', {'users': users})

        >>> @use_anonymized_data('custom_masked_role')
        >>> def api_endpoint(request):
        ...     return JsonResponse({'users': list(User.objects.values())})

        >>> # Class-based view example
        >>> class SensitiveDataView(View):
        ...     @method_decorator(use_anonymized_data)
        ...     def get(self, request):
        ...         data = SensitiveModel.objects.all()
        ...         return JsonResponse({'data': list(data.values())})

    Note:
        - Works with function-based views, class-based views, and regular functions
        - Automatically handles role switching and cleanup
        - Preserves function signatures and return values
        - Can be used with Django's method_decorator for class-based views
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with anonymized_data(role_name=role_name, auto_create=auto_create):
                return func(*args, **kwargs)

        return wrapper

    # Support both @use_anonymized_data and @use_anonymized_data() syntax
    if callable(role_name):
        # Called as @use_anonymized_data (without parentheses)
        func = role_name
        role_name = None
        return decorator(func)
    else:
        # Called as @use_anonymized_data() or @use_anonymized_data('role')
        return decorator


def database_role_required(role_name: str):
    """
    Decorator that ensures a specific database role is active during function execution.

    Args:
        role_name: Name of the database role to switch to

    Example:
        >>> @database_role_required('readonly_user')
        >>> def read_only_operation():
        ...     return MyModel.objects.all()

    Raises:
        RuntimeError: If the specified role doesn't exist
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from django_postgres_anon.context_managers import database_role

            with database_role(role_name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


class AnonymizedDataMixin:
    """
    Mixin for class-based views to automatically use anonymized data.

    This mixin ensures all database operations within the view use anonymized data
    by wrapping the dispatch method.

    Example:
        >>> class SensitiveReportView(AnonymizedDataMixin, ListView):
        ...     model = User
        ...     template_name = 'sensitive_report.html'
        ...     anonymized_role = 'custom_masked_role'  # Optional

        >>> class APIView(AnonymizedDataMixin, View):
        ...     def get(self, request):
        ...         users = User.objects.all()  # Automatically anonymized
        ...         return JsonResponse({'users': list(users.values())})
    """

    anonymized_role: Optional[str] = None
    auto_create_role: bool = True

    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to use anonymized data context"""
        with anonymized_data(role_name=self.anonymized_role, auto_create=self.auto_create_role):
            return super().dispatch(request, *args, **kwargs)


# Alias for common usage patterns
anonymized_view = use_anonymized_data  # More semantic alias for views
masked_data = use_anonymized_data  # Alternative name for clarity
