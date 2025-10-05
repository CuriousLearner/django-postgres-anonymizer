API Reference
=============

This page documents the public API of Django PostgreSQL Anonymizer.

Context Managers
----------------

.. autofunction:: django_postgres_anon.context_managers.anonymized_data

Decorators
----------

.. autofunction:: django_postgres_anon.decorators.use_anonymized_data

Mixins
------

.. autoclass:: django_postgres_anon.mixins.AnonymizedDataMixin
   :members:

Models
------

MaskingRule
~~~~~~~~~~~

Defines anonymization rules for database columns.

**Fields:**

* ``table_name`` - Database table name
* ``column_name`` - Column to anonymize
* ``function_expr`` - PostgreSQL Anonymizer function (e.g., ``anon.fake_email()``)
* ``enabled`` - Whether rule is active

MaskingPreset
~~~~~~~~~~~~~

Pre-configured sets of anonymization rules.

**Fields:**

* ``name`` - Preset identifier
* ``description`` - Human-readable description
* ``preset_type`` - Category (healthcare, finance, etc.)

MaskedRole
~~~~~~~~~~

PostgreSQL roles with anonymized data access.

**Fields:**

* ``role_name`` - PostgreSQL role name
* ``created_at`` - Creation timestamp

MaskingLog
~~~~~~~~~~

Audit trail for anonymization operations.

**Fields:**

* ``operation`` - Operation type (apply_rule, role_switch, etc.)
* ``user`` - User who performed operation
* ``timestamp`` - When operation occurred
* ``success`` - Whether operation succeeded
* ``error_message`` - Error details if failed
* ``details`` - Additional metadata (JSON)
* ``duration`` - Operation duration

Configuration
-------------

get_anon_setting
~~~~~~~~~~~~~~~~

Get a configuration setting value with environment variable support.

.. code-block:: python

   from django_postgres_anon.config import get_anon_setting

   # Get individual settings
   enabled = get_anon_setting('ENABLED')
   masked_groups = get_anon_setting('MASKED_GROUPS')
   validate = get_anon_setting('VALIDATE_FUNCTIONS')

Available settings: ``ENABLED``, ``MASKED_GROUPS``, ``DEFAULT_MASKED_ROLE``,
``ANONYMIZED_DATA_ROLE``, ``VALIDATE_FUNCTIONS``, ``ALLOW_CUSTOM_FUNCTIONS``, ``ENABLE_LOGGING``

See :doc:`settings` for details.

Utility Functions
-----------------

validate_anon_extension
~~~~~~~~~~~~~~~~~~~~~~~

Check if PostgreSQL Anonymizer extension is installed and available.

.. code-block:: python

   from django_postgres_anon.utils import validate_anon_extension

   if validate_anon_extension():
       print('Extension is installed')
   else:
       print('Extension not available')

Returns ``True`` if extension is installed, ``False`` otherwise.

Commonly used in health checks and validation scripts.

Management Commands
-------------------

anon_init
~~~~~~~~~

Initialize PostgreSQL anonymizer extension.

.. code-block:: bash

   python manage.py anon_init

Performs initial setup:

* Creates the ``anon`` extension in PostgreSQL
* Initializes anonymization system
* Sets up required database objects

Run this once after installation before using any other commands.

anon_apply
~~~~~~~~~~

Apply masking rules to the database.

.. code-block:: bash

   python manage.py anon_apply [--dry-run]

Options:

* ``--dry-run`` - Preview changes without applying them

Creates masking labels based on your ``MaskingRule`` configurations.

anon_status
~~~~~~~~~~~

Show anonymizer status and configuration.

.. code-block:: bash

   python manage.py anon_status

Displays:

* Extension installation status
* Active masking rules
* Database role configurations
* Current anonymization state

anon_validate
~~~~~~~~~~~~~

Validate anonymization rules and database setup.

.. code-block:: bash

   python manage.py anon_validate

Checks:

* PostgreSQL Anonymizer extension is installed
* All masking functions are valid
* No SQL injection patterns in rules
* Database permissions are correct

anon_dump
~~~~~~~~~

Create anonymized database dump.

.. code-block:: bash

   python manage.py anon_dump <output_file> [--format=custom]

Options:

* ``output_file`` - Path to dump file (required)
* ``--format`` - Dump format: ``custom``, ``plain``, ``directory``, ``tar`` (default: ``custom``)

Creates a PostgreSQL dump with anonymized data using ``pg_dump`` with anonymizer.

anon_drop
~~~~~~~~~

Remove anonymization from database.

.. code-block:: bash

   python manage.py anon_drop [--keep-extension]

Options:

* ``--keep-extension`` - Remove masking rules but keep the extension installed

**Warning:** This removes all masking labels and anonymization configuration.

anon_load_yaml
~~~~~~~~~~~~~~

Load anonymization rules from YAML presets.

.. code-block:: bash

   python manage.py anon_load_yaml <preset> [--overwrite] [--dry-run]

Options:

* ``preset`` - Preset name or path to YAML file
* ``--overwrite`` - Replace existing rules
* ``--dry-run`` - Preview what would be loaded

Built-in presets: ``django_auth``, ``ecommerce``, ``healthcare``, ``finance``, ``social_media``, ``education``

anon_fix_permissions
~~~~~~~~~~~~~~~~~~~~

Fix permissions for existing anonymized roles.

.. code-block:: bash

   python manage.py anon_fix_permissions

Repairs database role permissions if they become misconfigured.

See Also
--------

- :doc:`../getting-started/index` - Getting started
- :doc:`../guides/usage-patterns` - Usage patterns
- :doc:`settings` - Configuration reference
