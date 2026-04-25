# Debugging Guide's

## Log Files Location

```bash
# frappe-bench/logs/
frappe.log          # Main application log
error.log           # Errors
scheduler.log       # Scheduled job output
worker.log          # Background worker output

# Real-time tail
tail -f ~/frappe-bench/logs/frappe.log
tail -f ~/frappe-bench/logs/worker.log

# Site-specific logs
~/frappe-bench/sites/{sitename}/error.log
```

---

## Python Debugging

### In Controllers / Scripts
```python
import frappe

# Print to console (visible in bench start output)
print("Debug value:", self.some_field)
frappe.log(f"Processing {self.name}")

# Rich logging with structured data
frappe.logger().debug(f"Order {self.name} validated", extra={'doctype': 'Sales Order'})

# Inspect object
print(self.as_dict())

# Drop into PDB (only in dev!)
import pdb; pdb.set_trace()

# Log to Error Log (visible in Frappe UI at Error Log doctype)
frappe.log_error(
    title="My Custom Error",
    message=frappe.get_traceback()
)
```

### In bench console
```bash
bench --site mysite.localhost console
```
```python
# Inside console:
import frappe
frappe.init(site='mysite.localhost')
frappe.connect()

# Now you have full frappe context
doc = frappe.get_doc('Sales Order', 'SAL-ORD-00001')
print(doc.as_dict())

# Run any function
from my_app.utils import my_function
result = my_function(arg1, arg2)

# Execute SQL
results = frappe.db.sql("SELECT * FROM `tabSales Order` LIMIT 5", as_dict=True)
frappe.db.commit()  # if you changed data
```

### System Console (In Frappe UI)
Settings → System Console (or search "System Console"):
```python
# Runs in site context
doc = frappe.get_doc("Customer", "ACME-001")
print(doc.customer_name)
```

---

## JavaScript Debugging

### Browser DevTools
```javascript
// In any form script
console.log('frm.doc:', frm.doc);
console.log('Field value:', frm.get_value('customer'));

// Inspect frappe globals
console.log(frappe.session.user);
console.log(frappe.boot);
console.log(frappe.model.locals);  // All cached documents

// Network tab: watch XHR calls to /api/method and /api/resource
```

### Common JS Issues
```javascript
// "locals is not defined" — missing cdt/cdn context
frappe.ui.form.on('Child DocType', {
    qty: function(frm, cdt, cdn) {  // These are always needed for child fields
        let row = locals[cdt][cdn];  // Access child row
    }
});

// frm.call vs frappe.call
frm.call('method_name')           // Calls method on current document
frappe.call('app.module.method') // Calls any whitelisted function
```

---

## Common Error Patterns & Fixes

### Permission Errors
```
frappe.exceptions.PermissionError: You don't have permission to access...
```
**Fix:** Use `ignore_permissions=True` for system operations, or explicitly grant permissions. Check `frappe.has_permission()` before operations.

### Duplicate Entry
```
pymysql.err.IntegrityError: (1062, "Duplicate entry...")
```
**Fix:** Check `frappe.db.exists()` before insert. Or use `insert(ignore_if_duplicate=True)`.

### TimestampMismatch
```
frappe.exceptions.TimestampMismatchError
```
**Fix:** The document was modified by someone else. Reload and retry: `doc.reload()` then `doc.save()`.

### DocType Not Found
```
frappe.exceptions.DoesNotExistError: ...
```
**Fix:** Run `bench migrate`. The DocType JSON exists but wasn't synced to DB.

### Circular Import
```
ImportError: cannot import name X from partially initialized module
```
**Fix:** Move imports inside functions, use lazy imports, or restructure module hierarchy.

### White Screen / JS Error
```bash
# Rebuild assets
bench build --app my_app --force
# Clear browser cache
# Check browser console for the actual JS error
```

---

## Performance Debugging

### Slow Queries
```python
# Enable SQL debug in console
frappe.db.sql("SET GLOBAL general_log = 'ON'")

# Or use frappe's built-in query timing
import time
start = time.time()
result = frappe.db.sql("SELECT ...")
print(f"Query took {time.time() - start:.2f}s")

# Find slow queries via frappe
frappe.db.sql("SHOW PROCESSLIST")
frappe.db.sql("EXPLAIN SELECT * FROM `tabSales Order` WHERE ...")
```

### Database Index Check
```python
# Add missing index
frappe.db.add_index('Sales Order', ['customer', 'transaction_date'])
# Equivalent to: CREATE INDEX ON `tabSales Order`(customer, transaction_date)

# Check existing indexes
frappe.db.sql("SHOW INDEX FROM `tabSales Order`")
```

### Profiling
```python
# Profile a function
import cProfile
cProfile.run('my_function()')

# Frappe's built-in profiler
# In site_config.json: "enable_profiler": 1
# Then check /api/method/frappe.utils.response.respond → X-Frappe-Debug-Session header
```

### Memory Leaks
```bash
# Check process memory
ps aux --sort=-%mem | head -20

# In Python — find large objects
import sys
large_objects = [(sys.getsizeof(obj), type(obj)) for obj in gc.get_objects()]
large_objects.sort(reverse=True)
print(large_objects[:20])
```

---

## Frappe Doctor

```bash
bench --site mysite.localhost doctor
```
Checks:
- Scheduler status
- Worker status
- Database connectivity
- Redis connectivity
- Pending migrations
- App versions

---

## Test a Specific Patch

```bash
# Test in dev before running in prod
bench --site devsite.localhost run-patch my_app.patches.v1_1.my_patch
# Check logs/frappe.log for output
```

---

## Debug Hooks & Events

```python
# Add debug logging to doc_events temporarily
# In hooks.py:
doc_events = {
    "Sales Order": {
        "validate": "my_app.debug_utils.log_validate",
    }
}

# debug_utils.py
def log_validate(doc, method):
    frappe.log_error(
        title=f"Validate called on {doc.name}",
        message=str(doc.as_dict())
    )
```

---

## Version Compatibility Matrix

| Frappe Version | ERPNext Version | Python | Node | Branch |
|---------------|-----------------|--------|------|--------|
| 15.x | 15.x | 3.11+ | 18+ | version-15 |
| 14.x | 14.x | 3.10+ | 16+ | version-14 |
| 13.x | 13.x | 3.9+ | 14+ | version-13 |

Check installed versions:
```bash
bench version
bench --site mysite.localhost version
```
