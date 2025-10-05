# Security

Django PostgreSQL Anonymizer takes security seriously. This document
outlines security considerations, best practices, and how to report
security issues.

## Security Features

### Function Validation

All anonymization functions are validated to prevent SQL injection:

``` python
from django_postgres_anon.utils import validate_function_syntax

# Safe functions (allowed)
validate_function_syntax("anon.fake_email()")          # True
validate_function_syntax("anon.hash(column_name)")     # True
validate_function_syntax("anon.partial(email, 2, '*', 2)")  # True

# Dangerous functions (blocked)
validate_function_syntax("DROP TABLE users;")         # False
validate_function_syntax("anon.fake_email(); DROP")   # False
validate_function_syntax("custom_function()")         # False (unless enabled)
```

**Validation Rules:**

- Functions must be in the `anon` namespace (unless
  `ALLOW_CUSTOM_FUNCTIONS` is enabled)
- No SQL injection patterns (semicolons, comments, etc.)
- Proper PostgreSQL function syntax
- No dangerous SQL keywords

### Role-Based Access Control

Database-level security isolation using PostgreSQL roles:

``` sql
-- Masked role has limited permissions
CREATE ROLE masked_reader;

-- Grant only SELECT on anonymized views
GRANT SELECT ON anon.masked_view TO masked_reader;

-- Revoke access to original tables
REVOKE ALL ON sensitive_table FROM masked_reader;
```

**Role Isolation Benefits:**

- Original data never accessible from masked role
- Database-level security enforcement
- Privilege escalation prevention
- Connection pooling safety

### Audit Logging

Complete operation tracking for compliance:

``` python
from django_postgres_anon.models import MaskingLog

# All operations are logged
logs = MaskingLog.objects.filter(
    operation='apply_rule',
    success=True
).order_by('-timestamp')
```

**Logged Information:**

- User who performed the operation
- Timestamp and duration
- Operation type and parameters
- Success/failure status
- Error messages (sanitized)

### Secure Error Handling

Errors are handled without exposing sensitive information:

``` python
try:
    apply_anonymization_rule(rule)
except Exception as e:
    # Log detailed error internally
    logger.error(f"Rule application failed: {e}")

    # Return sanitized error to user
    return {"success": False, "error": "Rule application failed"}
```

## Security Best Practices

### Configuration Security

**1. Validate Configuration:**

``` python
# settings.py - Production configuration
POSTGRES_ANON = {
    'ENABLED': True,
    'VALIDATE_FUNCTIONS': True,       # Always validate functions
    'ALLOW_CUSTOM_FUNCTIONS': False,  # Restrict to anon namespace
    'ENABLE_LOGGING': True,           # Full audit trail
}
```

**2. Environment Variables:**

``` bash
# Use environment variables for sensitive settings
export POSTGRES_ANON_ENABLED=true
export POSTGRES_ANON_VALIDATE_FUNCTIONS=true
export POSTGRES_ANON_ALLOW_CUSTOM_FUNCTIONS=false
```

**3. Secret Management:**

``` python
# Don't commit database credentials
DATABASES = {
    'default': {
        'PASSWORD': os.environ.get('DB_PASSWORD'),  # From environment
        'USER': os.environ.get('DB_USER'),
    }
}
```

### Database Security

**1. Role Permissions:**

``` sql
-- Minimal permissions for masked role
CREATE ROLE masked_reader NOLOGIN;
GRANT CONNECT ON DATABASE myapp TO masked_reader;
GRANT USAGE ON SCHEMA anon TO masked_reader;
GRANT SELECT ON anon.masked_views TO masked_reader;

-- Explicit revocation
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM masked_reader;
```

**2. Connection Security:**

``` python
# Use SSL connections
DATABASES = {
    'default': {
        'OPTIONS': {
            'sslmode': 'require',
            'sslcert': '/path/to/client-cert.pem',
            'sslkey': '/path/to/client-key.pem',
            'sslrootcert': '/path/to/ca-cert.pem',
        }
    }
}
```

**3. Network Security:**

``` bash
# PostgreSQL configuration (postgresql.conf)
listen_addresses = 'localhost'  # Restrict network access
ssl = on                        # Enable SSL

# Host-based authentication (pg_hba.conf)
hostssl all masked_reader 10.0.0.0/8 md5  # SSL required
```

### Application Security

**1. User Authentication:**

``` python
# Ensure proper authentication before anonymization
@login_required
def sensitive_view(request):
    if request.user.groups.filter(name='analysts').exists():
        # Only authenticated users in specific groups
        pass
```

**2. Group Management:**

``` python
# Regularly audit group membership
from django.contrib.auth.models import Group, User

def audit_group_membership():
    analysts = Group.objects.get(name='analysts')
    members = analysts.user_set.all()

    # Log and review membership
    for user in members:
        logger.info(f"User {user.username} has analyst access")
```

**3. Session Security:**

``` python
# settings.py - Secure session configuration
SESSION_COOKIE_SECURE = True      # HTTPS only
SESSION_COOKIE_HTTPONLY = True    # No JavaScript access
SESSION_COOKIE_SAMESITE = 'Strict'  # CSRF protection
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
```

### Deployment Security

**1. Environment Separation:**

``` bash
# Development
export POSTGRES_ANON_ALLOW_CUSTOM_FUNCTIONS=true

# Production
export POSTGRES_ANON_ALLOW_CUSTOM_FUNCTIONS=false
export POSTGRES_ANON_VALIDATE_FUNCTIONS=true
```

**2. Access Control:**

``` yaml
# docker-compose.yml - Network isolation
services:
  web:
    networks:
      - frontend
  db:
    networks:
      - backend  # Isolated from external access
```

**3. Monitoring:**

``` python
# Monitor for suspicious activity
import logging

logger = logging.getLogger('django_postgres_anon.security')

def monitor_role_switches():
    # Alert on excessive role switching
    # Monitor failed authentication attempts
    # Track unusual data access patterns
    pass
```

## Common Security Issues

### SQL Injection Prevention

**Issue:** Malicious function expressions

``` python
# DANGEROUS - Don't do this
function_expr = request.POST.get('function')  # User input
MaskingRule.objects.create(function_expr=function_expr)
```

**Solution:** Always validate functions

``` python
# SAFE - Validate first
function_expr = request.POST.get('function')
if validate_function_syntax(function_expr):
    MaskingRule.objects.create(function_expr=function_expr)
else:
    raise ValidationError("Invalid function syntax")
```

### Privilege Escalation

**Issue:** Masked role with excessive permissions

``` sql
-- DANGEROUS
GRANT ALL PRIVILEGES ON ALL TABLES TO masked_reader;
```

**Solution:** Minimal permissions

``` sql
-- SAFE
GRANT SELECT ON specific_anonymized_view TO masked_reader;
```

### Data Leakage

**Issue:** Original data exposed in error messages

``` python
# DANGEROUS
try:
    user = User.objects.get(email=email)
except User.DoesNotExist:
    return f"User with email {email} not found"  # Exposes email
```

**Solution:** Sanitized error handling

``` python
# SAFE
try:
    user = User.objects.get(email=email)
except User.DoesNotExist:
    return "User not found"  # No sensitive data
```

## Security Monitoring

### Audit Logs

Monitor these events:

``` python
# Critical events to monitor
events_to_monitor = [
    'rule_creation',           # New anonymization rules
    'rule_modification',       # Changes to existing rules
    'role_switch_failure',     # Failed role switches
    'permission_escalation',   # Unauthorized access attempts
    'bulk_operations',         # Large-scale data operations
    'configuration_changes',   # Settings modifications
]
```

### Alerting

Set up alerts for suspicious activity:

``` python
# Example alerting logic
def check_security_alerts():
    # Alert on multiple failed role switches
    failed_switches = MaskingLog.objects.filter(
        operation='role_switch',
        success=False,
        timestamp__gte=timezone.now() - timedelta(minutes=5)
    ).count()

    if failed_switches > 5:
        send_security_alert("Multiple role switch failures detected")
```

### Performance Monitoring

Watch for performance anomalies that might indicate attacks:

``` python
# Monitor query performance
def monitor_query_performance():
    slow_queries = MaskingLog.objects.filter(
        duration__gt=timedelta(seconds=30)
    )

    if slow_queries.exists():
        # Investigate potential DoS or data extraction attempts
        pass
```

## Security Testing

### Penetration Testing

Test these scenarios:

1. **SQL Injection Attempts:**

    ``` python
    # Test malicious function expressions
    test_cases = [
        "anon.fake_email(); DROP TABLE users;",
        "'; DELETE FROM auth_user; --",
        "UNION SELECT password FROM auth_user",
    ]
    ```

2. **Privilege Escalation:**

    ``` python
    # Test role permissions
    with anonymized_data():
        try:
            # Should fail
            User.objects.create(is_superuser=True)
        except PermissionError:
            pass  # Expected behavior
    ```

3. **Data Extraction:**

    ``` python
    # Test for data leakage
    with anonymized_data():
        user = User.objects.first()
        assert '@anonymizer.com' in user.email  # Should be anonymized
    ```

### Automated Security Testing

``` python
# Add to test suite
class SecurityTestCase(TestCase):
    def test_sql_injection_prevention(self):
        """Test that malicious functions are rejected."""
        malicious_functions = [
            "DROP TABLE users;",
            "'; DELETE FROM auth_user; --",
            "UNION SELECT * FROM sensitive_table",
        ]

        for func in malicious_functions:
            with self.assertRaises(ValidationError):
                MaskingRule.objects.create(
                    table_name='test_table',
                    column_name='test_column',
                    function_expr=func
                )
```

## Compliance

### GDPR Compliance

The package supports GDPR requirements:

- **Right to Erasure:** Anonymization provides practical deletion
- **Data Minimization:** Only necessary fields are processed
- **Privacy by Design:** Anonymization at the database level
- **Audit Trail:** Complete logging for compliance reporting

### HIPAA Compliance

Healthcare data protection:

- **Administrative Safeguards:** Role-based access control
- **Physical Safeguards:** Database-level security
- **Technical Safeguards:** Encryption and audit logging
- **Minimum Necessary:** Anonymized data access

### SOX Compliance

Financial data requirements:

- **Internal Controls:** Automated rule application
- **Data Integrity:** Immutable audit logs
- **Access Controls:** Role-based permissions
- **Change Management:** Documented rule modifications

## Reporting Security Issues

**Do NOT** open public GitHub issues for security vulnerabilities.

**Instead, email:** <sanyam@sanyamkhurana.com>

**Include:**

- Detailed vulnerability description
- Steps to reproduce
- Potential impact assessment
- Suggested mitigation (if any)

**Response Timeline:**

- **Initial Response:** Within 24 hours
- **Triage:** Within 72 hours
- **Fix Development:** Varies by severity
- **Coordinated Disclosure:** After fix is available

**Severity Levels:**

- **Critical:** Immediate data exposure risk
- **High:** Privilege escalation or significant data risk
- **Medium:** Limited data exposure or DoS
- **Low:** Information disclosure or minor issues

## Security Updates

Security patches are released as soon as possible after discovery.

**Update Process:**

1. Security fix developed and tested
2. Security advisory published
3. Patch released with security note
4. Users notified through multiple channels

**Stay Informed:**

- Watch the GitHub repository for security advisories
- Subscribe to security notifications
- Monitor the changelog for security updates
- Follow \@CuriousLearner for announcements

Thank you for helping keep Django PostgreSQL Anonymizer secure!
