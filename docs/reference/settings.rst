Settings Reference
==================

This page documents all available configuration options for Django PostgreSQL Anonymizer.

Core Configuration
------------------

POSTGRES_ANON
~~~~~~~~~~~~~

The main configuration dictionary containing all anonymization settings.

.. code-block:: python

   # settings.py
   POSTGRES_ANON = {
       'ENABLED': True,
       'MASKED_GROUPS': ['analysts', 'qa_team'],
       'VALIDATE_FUNCTIONS': True,
       'ALLOW_CUSTOM_FUNCTIONS': False,
       'ENABLE_LOGGING': True,
   }

Individual Settings
-------------------

ENABLED
~~~~~~~

**Type:** ``bool``
**Default:** ``False``
**Environment Variable:** ``POSTGRES_ANON_ENABLED``

Controls whether anonymization is active throughout the application.

.. code-block:: python

   # Disable anonymization (useful for development)
   POSTGRES_ANON = {
       'ENABLED': False,
   }

**Environment Variable Usage:**

.. code-block:: bash

   export POSTGRES_ANON_ENABLED=true
   # or
   export POSTGRES_ANON_ENABLED=false

**Notes:**

- When disabled, all anonymization features are bypassed
- Middleware, context managers, and decorators become no-ops
- Useful for development environments where you need real data
- Can be toggled without code changes using environment variables

MASKED_GROUPS
~~~~~~~~~~~~~

**Type:** ``list[str]``
**Default:** ``['view_masked_data']``
**Environment Variable:** ``POSTGRES_ANON_MASKED_GROUPS``

List of Django user groups that should automatically see anonymized data.

.. code-block:: python

   POSTGRES_ANON = {
       'MASKED_GROUPS': ['analysts', 'qa_team', 'external_auditors'],
   }

**Environment Variable Usage:**

.. code-block:: bash

   # Comma-separated list
   export POSTGRES_ANON_MASKED_GROUPS=analysts,qa_team,external_auditors

**Notes:**

- Users in these groups see anonymized data automatically via middleware
- Group names must match Django auth groups exactly
- Empty list means no automatic anonymization
- Case-sensitive group name matching

VALIDATE_FUNCTIONS
~~~~~~~~~~~~~~~~~~

**Type:** ``bool``
**Default:** ``True``
**Environment Variable:** ``POSTGRES_ANON_VALIDATE_FUNCTIONS``

Whether to validate anonymization functions for security.

.. code-block:: python

   POSTGRES_ANON = {
       'VALIDATE_FUNCTIONS': True,  # Recommended
   }

**Environment Variable Usage:**

.. code-block:: bash

   export POSTGRES_ANON_VALIDATE_FUNCTIONS=true

**Security Impact:**

- Prevents SQL injection through function expressions
- Blocks dangerous SQL keywords and patterns
- **Strongly recommended** for all environments
- Disable only if you have custom validation logic

ALLOW_CUSTOM_FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~

**Type:** ``bool``
**Default:** ``False``
**Environment Variable:** ``POSTGRES_ANON_ALLOW_CUSTOM_FUNCTIONS``

Whether to allow custom functions outside the ``anon`` namespace.

.. code-block:: python

   # Development - allow custom functions for testing
   POSTGRES_ANON = {
       'ALLOW_CUSTOM_FUNCTIONS': True,
   }

   # Production - restrict to anon namespace only
   POSTGRES_ANON = {
       'ALLOW_CUSTOM_FUNCTIONS': False,
   }

**Environment Variable Usage:**

.. code-block:: bash

   export POSTGRES_ANON_ALLOW_CUSTOM_FUNCTIONS=false

**Security Considerations:**

- When ``False``: Only ``anon.*`` functions are allowed
- When ``True``: Any PostgreSQL function can be used
- Production environments should keep this ``False``
- Enable only for development or when you have custom anonymization functions

ENABLE_LOGGING
~~~~~~~~~~~~~~

**Type:** ``bool``
**Default:** ``True``
**Environment Variable:** ``POSTGRES_ANON_ENABLE_LOGGING``

Whether to log anonymization operations for audit purposes.

.. code-block:: python

   POSTGRES_ANON = {
       'ENABLE_LOGGING': True,
   }

**Environment Variable Usage:**

.. code-block:: bash

   export POSTGRES_ANON_ENABLE_LOGGING=true

**Logged Information:**

- Rule creation and modification
- Anonymization operations
- Role switching events
- Error conditions
- User and timestamp information

Environment-Specific Configurations
-----------------------------------

Development
~~~~~~~~~~~

.. code-block:: python

   # settings/development.py
   POSTGRES_ANON = {
       'ENABLED': True,
       'MASKED_GROUPS': ['developers'],
       'VALIDATE_FUNCTIONS': True,
       'ALLOW_CUSTOM_FUNCTIONS': True,    # OK for testing
       'ENABLE_LOGGING': True,
   }

Testing
~~~~~~~

.. code-block:: python

   # settings/testing.py
   POSTGRES_ANON = {
       'ENABLED': True,
       'MASKED_GROUPS': [],               # No automatic masking in tests
       'VALIDATE_FUNCTIONS': True,
       'ALLOW_CUSTOM_FUNCTIONS': False,
       'ENABLE_LOGGING': False,           # Reduce test noise
   }

Staging
~~~~~~~

.. code-block:: python

   # settings/staging.py
   POSTGRES_ANON = {
       'ENABLED': True,
       'MASKED_GROUPS': ['qa_team', 'stakeholders'],
       'VALIDATE_FUNCTIONS': True,
       'ALLOW_CUSTOM_FUNCTIONS': False,
       'ENABLE_LOGGING': True,
   }

Production
~~~~~~~~~~

.. code-block:: python

   # settings/production.py
   POSTGRES_ANON = {
       'ENABLED': True,
       'MASKED_GROUPS': ['analysts', 'external_auditors'],
       'VALIDATE_FUNCTIONS': True,        # ALWAYS in production
       'ALLOW_CUSTOM_FUNCTIONS': False,   # NEVER in production
       'ENABLE_LOGGING': True,            # ALWAYS for compliance
   }

12-Factor App Configuration
---------------------------

All settings support environment variables following 12-factor principles:

.. code-block:: bash

   # .env file or environment
   POSTGRES_ANON_ENABLED=true
   POSTGRES_ANON_MASKED_GROUPS=analysts,qa_team
   POSTGRES_ANON_VALIDATE_FUNCTIONS=true
   POSTGRES_ANON_ALLOW_CUSTOM_FUNCTIONS=false
   POSTGRES_ANON_ENABLE_LOGGING=true

Environment Variable Parsing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The configuration system automatically parses environment variables:

.. code-block:: text

   # Automatic boolean conversion
   'true', 'True', '1', 'yes', 'on' → True
   'false', 'False', '0', 'no', 'off' → False

   # Automatic list conversion (comma-separated)
   'analysts,qa_team' → ['analysts', 'qa_team']

   # Empty values
   '' → None (uses default)

Configuration Validation
------------------------

The package validates configuration on startup:

.. code-block:: python

   # Invalid configurations will raise errors
   POSTGRES_ANON = {
       'ENABLED': 'invalid',  # Must be boolean
       'MASKED_GROUPS': 'not_a_list',  # Must be list
   }

Validation Rules
~~~~~~~~~~~~~~~~

1. **ENABLED**: Must be boolean or boolean-like string
2. **MASKED_GROUPS**: Must be list of strings
3. **VALIDATE_FUNCTIONS**: Must be boolean
4. **ALLOW_CUSTOM_FUNCTIONS**: Must be boolean
5. **ENABLE_LOGGING**: Must be boolean

Common Configuration Issues
---------------------------

Issue: Anonymization Not Working
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Users in masked groups still see real data.

**Solution:**

.. code-block:: python

   # Check configuration
   POSTGRES_ANON = {
       'ENABLED': True,  # Must be True
       'MASKED_GROUPS': ['exact_group_name'],  # Must match Django groups exactly
   }

   # Verify middleware is installed
   MIDDLEWARE = [
       'django_postgres_anon.middleware.AnonymizationMiddleware',
       # ... other middleware
   ]

Issue: Permission Errors
~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Database permission errors when switching roles.

**Solution:**

.. code-block:: bash

   # Ensure PostgreSQL anonymizer extension is installed and configured
   python manage.py anon_init
   python manage.py anon_fix_permissions

Issue: Environment Variables Not Working
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Environment variables not being read.

**Solution:**

.. code-block:: python

   # Ensure django-environ or similar is configured
   import environ

   env = environ.Env()

   # Use environment variables
   POSTGRES_ANON = {
       'ENABLED': env.bool('POSTGRES_ANON_ENABLED', default=False),
       'MASKED_GROUPS': env.list('POSTGRES_ANON_MASKED_GROUPS', default=[]),
   }

Best Practices
--------------

1. **Use Environment Variables**: Never hard-code sensitive configuration
2. **Start with Safe Defaults**: Enable features gradually
3. **Test All Environments**: Verify configuration in dev, staging, and production
4. **Document Changes**: Track configuration changes in version control
5. **Monitor Settings**: Log configuration at startup for debugging
6. **Validate Early**: Catch configuration errors during deployment

Security Recommendations
------------------------

Production Security Checklist:

- ✅ ``ENABLED``: ``True`` (if using anonymization)
- ✅ ``VALIDATE_FUNCTIONS``: ``True`` (always)
- ✅ ``ALLOW_CUSTOM_FUNCTIONS``: ``False`` (unless required)
- ✅ ``ENABLE_LOGGING``: ``True`` (for compliance)
- ✅ Use environment variables for all settings
- ✅ Regularly audit ``MASKED_GROUPS`` membership

See Also
--------

- :doc:`../getting-started/index` - Configuration setup guide
- :doc:`../guides/usage-patterns` - Usage patterns and middleware
- :doc:`../examples/django-auth` - Real-world configuration examples
- :doc:`../deployment/production` - Production deployment settings
