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
       'AUTO_APPLY_RULES': False,         # NEVER enable in production
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
   export POSTGRES_ANON_AUTO_APPLY_RULES=false
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
      with anonymized_data():
          user = User.objects.first()
          assert '@anonymizer.com' in user.email
          print('✓ Anonymization verified')

Health Checks
-------------

Add anonymization health checks to your monitoring:

.. code-block:: python

   # health/views.py
   from django.http import JsonResponse
   from django_postgres_anon.utils import get_anon_extension_info
   from django_postgres_anon.config import get_config

   def anonymization_health(request):
       try:
           # Check extension availability
           extension_info = get_anon_extension_info()
           if not extension_info:
               return JsonResponse({
                   'status': 'error',
                   'message': 'Anonymizer extension not available'
               }, status=503)

           # Check configuration
           config = get_config()

           return JsonResponse({
               'status': 'healthy',
               'extension_version': extension_info['version'],
               'anonymization_enabled': config.enabled,
               'masked_groups': config.masked_groups
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

Performance Considerations
--------------------------

Database Optimization
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: sql

   -- Add indexes for frequently queried anonymization tables
   CREATE INDEX CONCURRENTLY idx_masking_rule_active
   ON django_postgres_anon_maskingrule(is_active)
   WHERE is_active = true;

   CREATE INDEX CONCURRENTLY idx_masking_log_timestamp
   ON django_postgres_anon_maskinglog(timestamp);

   -- Optimize group membership queries
   CREATE INDEX CONCURRENTLY idx_auth_user_groups_user
   ON auth_user_groups(user_id);

Caching Group Membership
~~~~~~~~~~~~~~~~~~~~~~~~

Cache user group membership to reduce database queries:

.. code-block:: python

   # utils.py
   from django.core.cache import cache

   def get_user_groups(user):
       cache_key = f'user_groups_{user.id}'
       groups = cache.get(cache_key)
       if groups is None:
           groups = list(user.groups.values_list('name', flat=True))
           cache.set(cache_key, groups, 300)  # 5 minutes
       return groups

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
      from django_postgres_anon.config import get_config
      config = get_config()
      print(f'Enabled: {config.enabled}')
      print(f'Groups: {config.masked_groups}')

Emergency Procedures
~~~~~~~~~~~~~~~~~~~~

If you need to quickly disable anonymization:

.. code-block:: bash

   # Method 1: Environment variable (requires restart)
   export POSTGRES_ANON_ENABLED=false

   # Method 2: Temporary Django setting override
   python manage.py shell -c "
   from django.conf import settings
   # Note: This only works if you restart the application

Compliance and Auditing
-----------------------

Audit Logs
~~~~~~~~~~

Monitor anonymization operations through the built-in logging:

.. code-block:: python

   # Generate audit report
   from django_postgres_anon.models import MaskingLog

   def audit_report(start_date, end_date):
       logs = MaskingLog.objects.filter(
           timestamp__range=[start_date, end_date]
       ).order_by('-timestamp')

       return {
           'total_operations': logs.count(),
           'successful_operations': logs.filter(success=True).count(),
           'failed_operations': logs.filter(success=False).count(),
           'operations_by_user': logs.values('user__username').annotate(
               count=Count('id')
           )
       }

See Also
--------

- :doc:`../getting-started/index` - Installation requirements
- :doc:`../reference/settings` - Configuration reference
- :doc:`../guides/usage-patterns` - Usage patterns and middleware
