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
