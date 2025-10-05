Production Deployment
=====================

This guide covers deploying Django PostgreSQL Anonymizer in production environments, focusing on package-specific configuration and best practices.

Production Configuration
------------------------

Security Settings
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # settings/production.py
   POSTGRES_ANON = {
       'ENABLED': True,
       'MASKED_GROUPS': ['analysts', 'external_auditors'],
       'VALIDATE_FUNCTIONS': True,        # ALWAYS enable
       'ALLOW_CUSTOM_FUNCTIONS': False,   # Restrict to anon namespace
       'ENABLE_LOGGING': True,            # Required for compliance
   }

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Production environment variables
   export POSTGRES_ANON_ENABLED=true
   export POSTGRES_ANON_MASKED_GROUPS=analysts,external_auditors
   export POSTGRES_ANON_VALIDATE_FUNCTIONS=true
   export POSTGRES_ANON_ALLOW_CUSTOM_FUNCTIONS=false
   export POSTGRES_ANON_ENABLE_LOGGING=true

Prerequisites
~~~~~~~~~~~~~

1. **PostgreSQL Anonymizer Extension** installed and configured
2. **Database roles** properly set up (``masked_reader``, etc.)
3. **Anonymization rules** tested and validated
4. **Backup strategy** that includes rule data

Deployment Process
------------------

Safe Deployment Steps
~~~~~~~~~~~~~~~~~~~~~

1. **Validate Configuration**:

   .. code-block:: bash

      # Test configuration before deployment
      python manage.py check
      python manage.py anon_status
      python manage.py anon_validate

2. **Deploy Application Code**:

   Deploy your Django application using your preferred method, ensuring the anonymization package is included.

3. **Apply Database Changes** (if any):

   .. code-block:: bash

      # Run migrations first
      python manage.py migrate

      # Then apply new anonymization rules (if any)
      python manage.py anon_apply

4. **Verify Anonymization**:

   .. code-block:: bash

      # Test that anonymization is working
      python manage.py shell -c "
      from django_postgres_anon.context_managers import anonymized_data
      from django.contrib.auth.models import User

      # Get original data
      original_user = User.objects.first()
      original_email = original_user.email if original_user else None

      # Get anonymized data
      with anonymized_data():
          anon_user = User.objects.first()
          anon_email = anon_user.email if anon_user else None

      # Verify emails are different (anonymization is working)
      if original_email and anon_email and original_email != anon_email:
          print('✓ Anonymization verified: email changed')
      else:
          print('✗ Anonymization may not be working')
      "

Health Checks
-------------

Add anonymization health checks to your monitoring:

.. code-block:: python

   # health/views.py
   from django.http import JsonResponse
   from django_postgres_anon.utils import validate_anon_extension
   from django_postgres_anon.config import get_anon_setting
   from django_postgres_anon.models import MaskingRule

   def anonymization_health(request):
       try:
           # Check extension availability
           extension_available = validate_anon_extension()
           if not extension_available:
               return JsonResponse({
                   'status': 'error',
                   'message': 'Anonymizer extension not installed'
               }, status=503)

           # Check configuration and rules
           enabled = get_anon_setting('ENABLED')
           masked_groups = get_anon_setting('MASKED_GROUPS')
           active_rules = MaskingRule.objects.filter(enabled=True).count()

           return JsonResponse({
               'status': 'healthy',
               'anonymization_enabled': enabled,
               'masked_groups': masked_groups,
               'active_rules': active_rules
           })

       except Exception as e:
           return JsonResponse({
               'status': 'error',
               'message': str(e)
           }, status=503)

Monitoring and Logging
----------------------

Configure logging for audit and troubleshooting:

.. code-block:: python

   # settings/production.py
   LOGGING = {
       'version': 1,
       'disable_existing_loggers': False,
       'handlers': {
           'file': {
               'level': 'INFO',
               'class': 'logging.handlers.RotatingFileHandler',
               'filename': '/var/log/django/anonymization.log',
               'maxBytes': 10485760,  # 10MB
               'backupCount': 5,
           },
       },
       'loggers': {
           'django_postgres_anon': {
               'handlers': ['file'],
               'level': 'INFO',
               'propagate': True,
           },
       },
   }

Security Best Practices
-----------------------

1. **Validate All Function Expressions**: Always keep ``VALIDATE_FUNCTIONS=True``
2. **Restrict Custom Functions**: Keep ``ALLOW_CUSTOM_FUNCTIONS=False`` in production
3. **Audit Group Membership**: Regularly review who has access to masked groups
4. **Monitor Role Switching**: Log and alert on unusual anonymization activity
5. **Backup Rule Data**: Include anonymization rules in your backup strategy

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

1. **Role Switching Failures**:

   .. code-block:: bash

      # Check if masked_reader role exists
      python manage.py shell -c "
      from django.db import connection
      with connection.cursor() as cursor:
          cursor.execute('SELECT rolname FROM pg_roles WHERE rolname = %s', ['masked_reader'])
          print('Role exists:', bool(cursor.fetchone()))

2. **Permission Errors**:

   .. code-block:: bash

      # Fix database permissions
      python manage.py anon_fix_permissions

3. **Configuration Issues**:

   .. code-block:: bash

      # Validate current configuration
      python manage.py shell -c "
      from django_postgres_anon.config import get_anon_setting
      print(f'Enabled: {get_anon_setting(\"ENABLED\")}')
      print(f'Groups: {get_anon_setting(\"MASKED_GROUPS\")}')

Emergency Procedures
~~~~~~~~~~~~~~~~~~~~

If you need to quickly disable anonymization:

.. code-block:: bash

   # Set environment variable and restart application
   export POSTGRES_ANON_ENABLED=false
   # Then restart your Django application

   # Or update settings.py and restart
   # POSTGRES_ANON = {'ENABLED': False}

Compliance and Auditing
-----------------------

Audit Logs
~~~~~~~~~~

Monitor anonymization operations through the built-in logging:

.. code-block:: python

   # Generate audit report
   from django.db.models import Count
   from django_postgres_anon.models import MaskingLog

   def audit_report(start_date, end_date):
       logs = MaskingLog.objects.filter(
           timestamp__range=[start_date, end_date]
       ).order_by('-timestamp')

       return {
           'total_operations': logs.count(),
           'successful_operations': logs.filter(success=True).count(),
           'failed_operations': logs.filter(success=False).count(),
           'operations_by_type': logs.values('operation').annotate(
               count=Count('id')
           ),
           'operations_by_user': logs.values('user').annotate(
               count=Count('id')
           )
       }

See Also
--------

- :doc:`../getting-started/index` - Installation requirements
- :doc:`../reference/settings` - Configuration reference
- :doc:`../guides/usage-patterns` - Usage patterns and middleware
