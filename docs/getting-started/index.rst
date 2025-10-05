Getting Started
===============

This guide will get you up and running with Django PostgreSQL Anonymizer in 10 minutes.

Requirements
------------

* Python 3.8+
* Django 3.2+
* PostgreSQL 12+ with Anonymizer extension

Step 1: Install PostgreSQL Anonymizer Extension
-----------------------------------------------

**Docker (Recommended for Development):**

.. code-block:: bash

   docker run -d \
     --name postgres-anon \
     -e POSTGRES_PASSWORD=postgres \
     -p 5432:5432 \
     registry.gitlab.com/dalibo/postgresql_anonymizer:14

**Ubuntu/Debian:**

.. code-block:: bash

   sudo apt update
   sudo apt install postgresql-14 postgresql-14-anonymizer

**macOS (Homebrew):**

.. code-block:: bash

   brew install postgresql@14 postgresql-anonymizer

**Verify Installation:**

.. code-block:: sql

   CREATE EXTENSION IF NOT EXISTS anon CASCADE;
   SELECT anon.init();

Step 2: Install Django Package
-------------------------------

.. code-block:: bash

   pip install django-postgres-anonymizer

Step 3: Configure Django
-------------------------

**Add to settings.py:**

.. code-block:: python

   INSTALLED_APPS = [
       # ... your apps
       'django_postgres_anon',
   ]

   POSTGRES_ANON = {
       'ENABLED': True,
       'MASKED_GROUPS': ['analysts', 'qa_team'],
   }

   # Optional: Add middleware for automatic anonymization
   MIDDLEWARE = [
       # ... other middleware
       'django_postgres_anon.middleware.AnonRoleMiddleware',
   ]

**Environment Variables (12-Factor Apps):**

.. code-block:: bash

   export POSTGRES_ANON_ENABLED=true
   export POSTGRES_ANON_MASKED_GROUPS=analysts,qa_team

Step 4: Initialize
-------------------

.. code-block:: bash

   python manage.py migrate
   python manage.py anon_init

Step 5: Create Anonymization Rules
-----------------------------------

**Option A: Use Built-in Presets**

.. code-block:: bash

   # Django auth tables
   python manage.py anon_load_yaml django_auth
   python manage.py anon_apply

**Option B: Create Custom Rules**

.. code-block:: python

   from django_postgres_anon.models import MaskingRule

   MaskingRule.objects.create(
       table_name='auth_user',
       column_name='email',
       function_expr='anon.fake_email()',
       enabled=True
   )

.. code-block:: bash

   python manage.py anon_apply

Step 6: Use Anonymized Data
----------------------------

**Automatic (Middleware):**

Users in ``MASKED_GROUPS`` automatically see anonymized data:

.. code-block:: python

   # Any user in 'analysts' group sees anonymized data
   User.objects.all()  # Emails are anonymized

**Manual (Context Manager):**

.. code-block:: python

   from django_postgres_anon.context_managers import anonymized_data

   with anonymized_data():
       users = User.objects.all()  # Anonymized
       export_to_csv(users)

**Decorator:**

.. code-block:: python

   from django_postgres_anon.decorators import use_anonymized_data

   @use_anonymized_data
   def analytics_report(request):
       return JsonResponse({
           'users': list(User.objects.values('email'))
       })

Configuration Reference
-----------------------

**Common Settings:**

.. code-block:: python

   POSTGRES_ANON = {
       # Enable/disable anonymization
       'ENABLED': True,

       # User groups that see anonymized data
       'MASKED_GROUPS': ['analysts', 'qa_team'],

       # Security
       'VALIDATE_FUNCTIONS': True,
       'ALLOW_CUSTOM_FUNCTIONS': False,

       # Audit logging
       'ENABLE_LOGGING': True,
   }

**Environment-Specific:**

Development:

.. code-block:: python

   POSTGRES_ANON = {
       'ENABLED': True,
       'MASKED_GROUPS': ['developers'],
   }

Production:

.. code-block:: python

   import os

   POSTGRES_ANON = {
       'ENABLED': os.getenv('POSTGRES_ANON_ENABLED', 'false').lower() == 'true',
       'MASKED_GROUPS': os.getenv('POSTGRES_ANON_MASKED_GROUPS', '').split(','),
       'VALIDATE_FUNCTIONS': True,
       'ENABLE_LOGGING': True,
   }

Cloud Platform Notes
--------------------

⚠️ **Managed PostgreSQL services (AWS RDS, Azure, GCP, Heroku) do not support the Anonymizer extension.**

**Alternatives:**

* Docker containers with self-managed PostgreSQL
* Virtual machines (EC2, Compute Engine, Azure VMs)
* Self-hosted PostgreSQL

Next Steps
----------

* :doc:`../guides/usage-patterns` - Learn different usage patterns
* :doc:`../reference/settings` - Complete configuration reference
* :doc:`../examples/django-auth` - Real-world example
* :doc:`../deployment/production` - Production deployment guide
