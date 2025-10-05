Usage Patterns
==============

Django PostgreSQL Anonymizer provides three ways to access anonymized data. Choose the pattern that fits your use case.

Quick Reference
---------------

.. list-table::
   :header-rows: 1
   :widths: 20 30 25 25

   * - Pattern
     - When to Use
     - Scope
     - Setup Required
   * - **Middleware**
     - Automatic for user groups
     - Entire request
     - Minimal (settings)
   * - **Context Manager**
     - Manual, specific queries
     - Code block
     - None
   * - **Decorator**
     - Entire view/function
     - Function scope
     - None

Pattern 1: Middleware (Automatic)
----------------------------------

**Best for:** Production apps where certain user groups should always see anonymized data.

**Configuration:**

.. code-block:: python

   # settings.py
   MIDDLEWARE = [
       # ... other middleware
       'django_postgres_anon.middleware.AnonRoleMiddleware',
   ]

   POSTGRES_ANON = {
       'ENABLED': True,
       'MASKED_GROUPS': ['analysts', 'qa_team', 'external_auditors'],
   }

**How it works:**

1. User logs in
2. Middleware checks if user is in ``MASKED_GROUPS``
3. If yes, switches to anonymized role for the entire request
4. All queries automatically return anonymized data

**Example:**

.. code-block:: python

   # No code changes needed!
   # Users in 'analysts' group automatically see anonymized data

   def dashboard(request):
       users = User.objects.all()  # Anonymized for analysts
       return render(request, 'dashboard.html', {'users': users})

Pattern 2: Context Manager (Manual)
------------------------------------

**Best for:** Specific code blocks that need anonymized data, regardless of user.

**Usage:**

.. code-block:: python

   from django_postgres_anon.context_managers import anonymized_data

   def generate_report(request):
       # Regular data
       total_users = User.objects.count()

       # Anonymized data for export
       with anonymized_data():
           users = User.objects.all()
           export_to_csv(users)

       return JsonResponse({'total': total_users})

**Advanced - Custom Role:**

.. code-block:: python

   # Use a specific masked role
   with anonymized_data('custom_masked_role'):
       sensitive_data = SensitiveModel.objects.all()

Pattern 3: Decorator (View-Level)
----------------------------------

**Best for:** Entire views or functions that should always use anonymized data.

**Usage:**

.. code-block:: python

   from django_postgres_anon.decorators import use_anonymized_data

   @use_anonymized_data
   def analytics_api(request):
       return JsonResponse({
           'users': list(User.objects.values('email', 'username'))
       })

**Class-Based Views:**

.. code-block:: python

   from django.utils.decorators import method_decorator

   class AnalyticsView(View):
       @method_decorator(use_anonymized_data)
       def get(self, request):
           data = User.objects.all()
           return JsonResponse({'data': list(data.values())})

**Or use the Mixin:**

.. code-block:: python

   from django_postgres_anon.mixins import AnonymizedDataMixin

   class ReportView(AnonymizedDataMixin, ListView):
       model = SensitiveModel  # All queries automatically anonymized
       template_name = 'report.html'

Combining Patterns
------------------

You can use multiple patterns together:

.. code-block:: python

   # Middleware enabled globally for 'analysts' group
   # But you can also use context managers for specific cases

   def admin_export(request):
       # This view accessible by admins only
       # But we still want to export anonymized data

       if not request.user.is_staff:
           return HttpResponseForbidden()

       with anonymized_data():
           users = User.objects.all()
           return export_csv(users)

Common Patterns
---------------

**Pattern: Public API Endpoints**

.. code-block:: python

   @use_anonymized_data
   def public_api(request):
       # All data automatically anonymized
       return JsonResponse({
           'users': list(User.objects.values())
       })

**Pattern: Conditional Anonymization**

.. code-block:: python

   def smart_view(request):
       if should_anonymize(request):
           with anonymized_data():
               data = get_data()
       else:
           data = get_data()

       return render(request, 'template.html', {'data': data})

**Pattern: Multiple Roles**

.. code-block:: python

   def tiered_access(request):
       if request.user.groups.filter(name='full_access').exists():
           data = SensitiveModel.objects.all()  # Real data
       elif request.user.groups.filter(name='limited_access').exists():
           with anonymized_data():
               data = SensitiveModel.objects.all()  # Anonymized
       else:
           data = SensitiveModel.objects.none()  # No access

       return render(request, 'data.html', {'data': data})

Troubleshooting
---------------

**Issue: Anonymization not working**

.. code-block:: python

   # Check if extension is installed
   from django_postgres_anon.utils import validate_anon_extension

   if not validate_anon_extension():
       print("PostgreSQL Anonymizer extension not installed!")

**Issue: Permission errors**

.. code-block:: bash

   # Fix permissions
   python manage.py anon_fix_permissions

**Issue: Role not found**

The middleware/context manager creates roles automatically by default. If disabled:

.. code-block:: python

   from django_postgres_anon.utils import create_masked_role

   create_masked_role('masked_reader')

See Also
--------

- :doc:`../getting-started/index` - Initial setup
- :doc:`../reference/settings` - Configuration options
- :doc:`../examples/django-auth` - Real-world example
