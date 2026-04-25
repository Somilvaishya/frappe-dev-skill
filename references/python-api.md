# Python API Reference

## frappe.* Global Namespace

### Document Operations
```python
frappe.get_doc(doctype, name)              # Load full document
frappe.get_doc({'doctype': 'X', ...})      # New doc from dict (unsaved)
frappe.new_doc(doctype)                    # New empty document
frappe.get_cached_doc(doctype, name)       # Cached version (read-only)
frappe.get_last_doc(doctype)               # Most recently modified
frappe.copy_doc(doc)                       # Deep copy
frappe.rename_doc(doctype, old, new, force=False)
frappe.delete_doc(doctype, name, force=False, ignore_permissions=False)
```

### Database Query (frappe.db)
```python
frappe.db.get_value(dt, filters, fieldname, as_dict=False)
frappe.db.get_values(dt, filters, fieldnames, as_dict=True)
frappe.db.get_all(dt, filters, fields, order_by, limit, as_list=False)
frappe.db.get_list(dt, ...)               # Respects permissions
frappe.db.set_value(dt, name, fieldname, value)
frappe.db.set_value(dt, name, {f1: v1, f2: v2})
frappe.db.count(dt, filters)
frappe.db.exists(dt, name_or_filters)     # Returns name if exists, else None
frappe.db.delete(dt, filters)             # Batch delete
frappe.db.sql(query, values, as_dict, as_list, debug)
frappe.db.commit()                        # Explicit commit (scripts only)
frappe.db.rollback()
frappe.db.add_index(dt, fields)
frappe.db.get_single_value(dt, field)     # Single DocType value
frappe.db.set_single_value(dt, field, value)

# Filters syntax:
# Simple: {'status': 'Open', 'customer': 'ACME'}
# Operators: {'qty': ['>', 0]}, {'status': ['in', ['Open', 'Draft']]}
# Not: {'status': ['!=', 'Cancelled']}
# Like: {'name': ['like', 'SAL-%']}
# Between: {'date': ['between', ['2024-01-01', '2024-12-31']]}
```

### User & Session
```python
frappe.session.user                        # Current user email
frappe.session.sid                         # Session ID
frappe.get_user()                          # User object
frappe.session.data.user_type             # 'System User' or 'Website User'
frappe.local.conf                          # site_config.json as dict
frappe.conf                                # Same as above
```

### Messaging & UI
```python
frappe.throw(msg, exc=frappe.ValidationError, title=None)  # Raise + show error
frappe.msgprint(msg, title='Message', indicator='blue')    # Non-blocking message
frappe.log_error(title, message)           # Log to Error Log doctype
frappe.log(msg)                            # Debug log
frappe.logger().debug/info/warning/error() # Structured logging
frappe.publish_realtime(event, message, room, user)        # Socket.io push
frappe.publish_progress(percent, title, description)       # Progress bar
```

### Permissions
```python
frappe.has_permission(doctype, ptype='read', doc=None, user=None)
frappe.only_if_user_is_logged_in(ptype='read')
frappe.local.login_manager.check_if_enabled(email)
frappe.get_roles(username)                 # List of roles
frappe.has_role(role, user=None)
```

### Utilities
```python
frappe.utils.now()                         # '2024-01-15 10:30:00'
frappe.utils.nowdate()                     # '2024-01-15'
frappe.utils.get_datetime(string)          # Parse to datetime
frappe.utils.add_days(date, n)            # Date arithmetic
frappe.utils.date_diff(end, start)        # Days between dates
frappe.utils.flt(value, precision=None)   # Safe float conversion
frappe.utils.cint(value)                  # Safe int conversion
frappe.utils.cstr(value)                  # Safe str conversion
frappe.utils.get_url()                    # Site URL
frappe.utils.get_link_to_form(dt, name)  # HTML link to form
frappe.utils.random_string(length)
frappe.utils.make_filter_tuple(filters)
frappe.utils.get_fullname(user)
frappe.utils.send_email(recipients, subject, message, ...)
frappe.utils.pdf_body_html(html)          # HTML to PDF
```

### Cache
```python
cache = frappe.cache()
cache.set_value(key, value, expires_in_sec=86400)
cache.get_value(key, generator=None)       # generator = fallback function
cache.delete_value(key)
cache.hset(name, key, value)
cache.hget(name, key)
cache.hdel(name, key)

# Document-level cache
frappe.clear_cache(doctype='Sales Order')  # Clear specific doctype
frappe.clear_cache()                        # Clear all cache
```

### Background Jobs
```python
frappe.enqueue(
    method,                    # 'module.function' string or callable
    queue='default',           # 'short'|'default'|'long'
    timeout=300,               # seconds
    is_async=True,
    now=False,                 # If True, run synchronously
    job_id=None,               # Unique ID to prevent duplicates
    deduplicate=False,
    **kwargs                   # Passed to the function
)

frappe.enqueue_doc(
    doctype, name, method,     # Call a whitelisted doc method async
    queue='default', **kwargs
)
```

### Email
```python
frappe.sendmail(
    recipients=['user@example.com'],
    subject='Subject',
    message='<p>HTML body</p>',
    attachments=[{'fname': 'file.pdf', 'fcontent': bytes}],
    cc=[],
    bcc=[],
    reply_to=None,
    send_after=None,           # datetime for scheduled send
    reference_doctype='Sales Order',
    reference_name='SAL-ORD-00001'
)
```

### Jinja / Templates
```python
frappe.render_template(template_string, context_dict)
frappe.get_template(path)                  # Load .html template
# In print formats — available Jinja context:
# doc, frappe, utils, filters
```

### API Exposure
```python
@frappe.whitelist()
def my_function(arg1, arg2=None):
    """Accessible at /api/method/my_app.module.my_function"""
    frappe.has_permission('My DocType', throw=True)
    return {'result': 'value'}

@frappe.whitelist(allow_guest=True)
def public_endpoint():
    """Accessible without login"""
    pass

@frappe.whitelist(methods=['POST'])
def post_only():
    pass
```

### Transactions & Context
```python
with frappe.db.savepoint():
    # partial rollback on exception
    risky_operation()

# Ignore links (foreign key) during delete
frappe.delete_doc('Sales Order', name, ignore_permissions=True, 
                   force=True, ignore_missing=True)

# Flags (in-request signaling)
frappe.flags.in_migrate              # True during bench migrate
frappe.flags.in_install              # True during app install
frappe.flags.ignore_permissions      # Skip permission checks
frappe.local.flags.in_patch          # True during patch
```

### Meta & Schema
```python
frappe.get_meta(doctype)               # DocType meta object
meta = frappe.get_meta('Sales Order')
meta.fields                            # List of DocField objects
meta.get_field('customer')             # Single field meta
meta.has_field('fieldname')
meta.get_link_fields()
meta.get_table_fields()
meta.get_select_fields()
frappe.get_all_linked_doctypes('Sales Order')
```
