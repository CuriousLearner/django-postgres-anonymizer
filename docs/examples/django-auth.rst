Example: Django User Model
===========================

Complete example of anonymizing Django's built-in User model.

Setup
-----

**1. Load the Django Auth preset:**

.. code-block:: bash

   python manage.py anon_load_yaml django_auth

**2. Apply anonymization rules:**

.. code-block:: bash

   python manage.py anon_apply

**3. Configure user groups:**

.. code-block:: python

   # settings.py
   POSTGRES_ANON = {
       'ENABLED': True,
       'MASKED_GROUPS': ['analysts', 'qa_team'],
   }

What Gets Anonymized
--------------------

The ``django_auth`` preset anonymizes:

* **Email:** ``john@example.com`` → Fake email (e.g., ``alice.smith@example.com``)
* **First Name:** ``John`` → Fake first name (e.g., ``Alice``)
* **Last Name:** ``Doe`` → Fake last name (e.g., ``Smith``)
* **Username:** Not anonymized by default (disabled to preserve login functionality)

Usage Examples
--------------

**Middleware (Automatic):**

.. code-block:: python

   # Any user in 'analysts' group sees anonymized data automatically
   def user_list(request):
       users = User.objects.all()  # Anonymized for analysts
       return render(request, 'users.html', {'users': users})

**Context Manager (Manual):**

.. code-block:: python

   from django_postgres_anon.context_managers import anonymized_data

   def export_users(request):
       with anonymized_data():
           users = User.objects.all()
           return export_to_csv(users)  # Anonymized data exported

**Decorator (View-Level):**

.. code-block:: python

   from django_postgres_anon.decorators import use_anonymized_data

   @use_anonymized_data
   def analytics_api(request):
       return JsonResponse({
           'users': list(User.objects.values('username', 'email', 'date_joined'))
       })

Custom Rules
------------

Add custom anonymization beyond the preset:

.. code-block:: python

   from django_postgres_anon.models import MaskingRule

   # Anonymize additional User field
   MaskingRule.objects.create(
       table_name='auth_user',
       column_name='date_joined',
       function_expr='anon.random_date_between(\'2020-01-01\'::date, \'2024-01-01\'::date)',
       enabled=True
   )

   # Or anonymize related profile
   MaskingRule.objects.create(
       table_name='user_profile',
       column_name='phone_number',
       function_expr='anon.fake_phone()',
       enabled=True
   )

Verification
------------

Test that anonymization works:

.. code-block:: python

   from django_postgres_anon.context_managers import anonymized_data
   from django.contrib.auth.models import User

   # Real data
   user = User.objects.first()
   print(user.email)  # john@example.com

   # Anonymized data
   with anonymized_data():
       user = User.objects.first()
       print(user.email)  # user_12345@anonymizer.com

See Also
--------

- :doc:`../guides/usage-patterns` - More usage patterns
- :doc:`../getting-started/index` - Getting started guide
- :doc:`../reference/settings` - Configuration options
