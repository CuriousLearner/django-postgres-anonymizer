# Django PostgreSQL Anonymizer Example Project

This example project demonstrates how to integrate and use django-postgres-anonymizer in a Django application.

## Features Demonstrated

- **Sample Models**: Customer, Order, Payment, SupportTicket, and UserActivity models with realistic PII data
- **Anonymization Rules**: Examples of creating and applying masking rules
- **Presets**: Loading and using pre-built anonymization presets
- **Admin Integration**: Django admin interface with anonymization actions
- **Interactive Demo**: Web interface to explore anonymization features
- **Context Managers**: Temporary anonymized data access with `anonymized_data()` and `database_role()`
- **Decorators**: Function and class-based view decorators for automatic anonymization
- **Function Validation**: Real-time validation and testing of anonymization functions
- **Data Comparison**: Side-by-side comparison of original vs anonymized data
- **Environment Configuration**: Environment-based settings for different deployment scenarios

## Setup Instructions

### Prerequisites

1. **PostgreSQL with Anonymizer Extension**

   ```bash
   # Install PostgreSQL and the anonymizer extension
   # See https://postgresql-anonymizer.readthedocs.io/en/latest/installation/
   ```

2. **Python Dependencies**

   ```bash
   pip install -r ../requirements.txt
   pip install -e ..  # Install django-postgres-anonymizer package
   ```

### Database Setup

1. **Create Database**

   ```bash
   createdb postgres_anon_example
   ```

2. **Configure Environment Variables** (optional)

   ```bash
   export DB_NAME=postgres_anon_example
   export DB_USER=postgres
   export DB_PASSWORD=your_password
   export DB_HOST=localhost
   export DB_PORT=5432
   ```

3. **Run Migrations**

   ```bash
   python manage.py migrate
   ```

4. **Create Superuser**

   ```bash
   python manage.py createsuperuser
   ```

### Initialize Anonymizer

1. **Initialize PostgreSQL Anonymizer Extension**

   ```bash
   python manage.py anon_init
   ```

2. **Load Sample Presets** (optional)

   ```bash
   python manage.py anon_load_yaml ../django_postgres_anon/config/presets/django_auth.yaml
   ```

### Run the Demo

1. **Start Development Server**

   ```bash
   python manage.py runserver
   ```

2. **Access the Application**
   - Demo homepage: <http://localhost:8000/>
   - Django Admin: <http://localhost:8000/admin/>
   - Sample data: <http://localhost:8000/sample/>
   - Anonymization demo: <http://localhost:8000/sample/anonymization-demo/>

## Demo Workflow

### 1. Create Sample Data

Visit `/sample/demo-data/` or run:

```bash
python manage.py shell -c "
from sample_app.views import create_demo_data
from django.http import HttpRequest
request = HttpRequest()
request.method = 'POST'
create_demo_data(request)
"
```

### 2. Explore the Data

- Browse customers at `/sample/customers/`
- View orders at `/sample/orders/`
- Check the Django admin at `/admin/`

### 3. Set Up Anonymization

Visit `/sample/anonymization-demo/` to:

- Create sample masking rules
- Load pre-built presets
- View schema information
- See before/after examples

### 4. Apply Anonymization

```bash
# Dry run to see what would be anonymized
python manage.py anon_apply --dry-run

# Apply anonymization rules
python manage.py anon_apply

# Check status
python manage.py anon_status
```

### 5. Export Anonymized Data

```bash
# Create anonymized database dump
python manage.py anon_dump anonymized_data.sql

# View the generated SQL file
head -n 50 anonymized_data.sql
```

## Key Features Demonstrated

### Models with PII Data

The sample app includes models with various types of sensitive data:

- **Customer**: SSN, address, phone, financial information
- **Order**: Shipping addresses, notes with potential PII
- **Payment**: Card information, billing addresses
- **SupportTicket**: Customer communications, internal notes
- **UserActivity**: IP addresses, session data, location info

### Anonymization Strategies

1. **Email Masking**: Replace with fake emails
2. **SSN Anonymization**: Generate fake SSNs
3. **Address Scrambling**: Use fake addresses
4. **Text Replacement**: Replace notes with Lorem Ipsum
5. **Numeric Noise**: Add statistical noise to financial data
6. **Partial Masking**: Show only first/last characters

### Management Commands

All django-postgres-anonymizer management commands are available:

```bash
# Initialize extension
python manage.py anon_init

# Apply anonymization rules
python manage.py anon_apply [--table TABLE] [--dry-run]

# Check anonymization status
python manage.py anon_status [--verbose]

# Create anonymized dump
python manage.py anon_dump output.sql [--format FORMAT]

# Load rules from YAML
python manage.py anon_load_yaml preset.yaml [--preset-name NAME]

# Validate existing rules
python manage.py anon_validate

# Drop anonymization
python manage.py anon_drop [--confirm]
```

### Admin Interface

The Django admin provides:

- Rule management with bulk actions
- Preset creation and activation
- Anonymization logs and monitoring
- Schema introspection tools

## Security Considerations

This example project demonstrates security best practices:

1. **Function Validation**: Only allow safe anonymization functions
2. **SQL Injection Prevention**: Parameterized queries and validation
3. **Role-Based Access**: Separate roles for anonymized data access
4. **Audit Logging**: Track all anonymization operations
5. **Constraint Awareness**: Handle unique constraints properly

## Customization

### Adding Custom Models

1. Create your models with PII data
2. Add them to `INSTALLED_APPS`
3. Create anonymization rules in the admin or via YAML
4. Test with `anon_apply --dry-run`

### Custom Anonymization Functions

While the extension provides many built-in functions, you can create custom ones:

```sql
-- Example custom function
CREATE OR REPLACE FUNCTION anon.fake_department_code()
RETURNS TEXT AS $$
SELECT 'DEPT-' || lpad((random() * 999)::INT::TEXT, 3, '0');
$$ LANGUAGE SQL;
```

### Environment-Specific Settings

Use different settings for development, staging, and production:

```python
# settings_production.py
DJANGO_POSTGRES_ANON = {
    'AUTO_APPLY_RULES': False,  # Never auto-apply in production
    'VALIDATE_FUNCTIONS': True,  # Always validate
    'ALLOW_CUSTOM_FUNCTIONS': False,  # Restrict to built-in functions
}
```

## Troubleshooting

### Common Issues

1. **Extension Not Found**

   ```
   ERROR: extension "anon" is not available
   ```

   Solution: Install postgresql-anonymizer extension

2. **Permission Errors**

   ```
   ERROR: permission denied to create extension "anon"
   ```

   Solution: Run as superuser or grant necessary permissions

3. **Unique Constraint Violations**

   ```
   ERROR: duplicate key value violates unique constraint
   ```

   Solution: Use `depends_on_unique=True` in rule or different function

### Debugging

Enable detailed logging:

```python
LOGGING = {
    'loggers': {
        'django_postgres_anon': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

## Next Steps

- Explore the source code in `../django_postgres_anon/`
- Read the full documentation
- Try creating custom anonymization rules
- Test with your own data models
- Consider security implications for your use case

## Support

For issues and questions:

- Check the main project README
- Review the test suite for examples
- Open issues on GitHub
