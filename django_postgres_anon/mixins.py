"""Class-based view mixins for Django PostgreSQL Anonymizer"""

from typing import Optional

from django_postgres_anon.context_managers import anonymized_data


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
