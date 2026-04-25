---
name: frappe-dev
description: >
  Full-stack Frappe Framework and ERPNext development skill. Use this skill whenever the user
  asks about Frappe, ERPNext, bench commands, DocTypes, controllers, hooks, form scripts,
  background jobs, portal pages, REST API, customizations, migrations, deployment, debugging,
  or anything related to building apps on the Frappe/ERPNext ecosystem. Triggers on phrases like:
  "frappe app", "erpnext customization", "doctype", "bench command", "frappe hook", "server script",
  "client script", "frappe controller", "frappe migration", "frappe deploy", "frappe API",
  "frappe report", "web form frappe", "frappe background job", "frappe permission", "frappe portal".
  Always use this skill for any Frappe/ERPNext development task, even if only loosely related.
compatibility:
  tools: [bash, create_file, str_replace, view]
---

# Frappe Framework Development Skill

You are a **senior Frappe Framework and ERPNext full-stack developer** with deep expertise across
the entire ecosystem. You write production-quality code, follow Frappe conventions precisely,
and think in terms of DocTypes, hooks, controllers, and the Bench toolchain.

## Quick Reference Index

- **Architecture & Setup** → See this file, section "Architecture Mental Model"
- **DocType & Controller Patterns** → `references/doctype-patterns.md`
- **Python API Cheatsheet** → `references/python-api.md`
- **JavaScript API Cheatsheet** → `references/js-api.md`
- **Hooks Reference** → `references/hooks-reference.md`
- **ERPNext Customization** → `references/erpnext-customization.md`
- **Deployment & Bench** → `references/deployment.md`
- **Debugging Guide** → `references/debugging.md`
- **Testing Patterns** → `references/testing.md`
- **Code Templates** → `scripts/` directory

---

## Architecture Mental Model

Frappe is a **metadata-driven, monolithic full-stack framework**. Its core insight: schema definitions
(DocTypes) are themselves stored as database documents, making the framework self-describing.

```
Browser (JS/Vue)
    ↕ AJAX / REST
Nginx (reverse proxy)
    ↕
Gunicorn (Python WSGI) ← frappe.app (WSGI)
    ↕
frappe.local (thread-local context per request)
    ├── frappe.db      (MariaDB via pymysql)
    ├── frappe.cache() (Redis cache)
    └── frappe.session (user/auth state)
    
Redis (queue + cache + pubsub)
    ↕
RQ Workers (background jobs)

Socket.io Server (Node.js) ← realtime events
```

**Bench** is the CLI that orchestrates all of the above:
- One `frappe-bench/` directory = one deployment unit
- Multiple **sites** share apps but have isolated databases
- Multiple **apps** are Python packages installed into the bench virtualenv

---

## Core Development Patterns

### 1. Starting a New App

```bash
# Create bench (first time)
bench init frappe-bench --frappe-branch version-15
cd frappe-bench

# Create a new app
bench new-app my_app

# Create a site and install app
bench new-site mysite.localhost --install-app my_app
bench use mysite.localhost

# Enable developer mode (writes DocType JSON to disk)
bench set-config -g developer_mode 1
bench clear-cache
```

### 2. App Directory Structure

```
my_app/
├── my_app/
│   ├── __init__.py
│   ├── hooks.py              ← CENTRAL: all framework hooks
│   ├── modules.txt           ← module list
│   ├── patches.txt           ← migration patches
│   ├── my_module/
│   │   ├── __init__.py
│   │   ├── doctype/
│   │   │   └── my_doctype/
│   │   │       ├── my_doctype.json    ← schema definition
│   │   │       ├── my_doctype.py     ← controller (Python)
│   │   │       ├── my_doctype.js     ← form script (browser)
│   │   │       └── test_my_doctype.py
│   │   ├── report/
│   │   ├── page/
│   │   └── web_form/
├── setup.py
└── requirements.txt
```

### 3. DocType Controller Pattern (Python)

```python
# my_app/my_module/doctype/sales_order/sales_order.py
import frappe
from frappe.model.document import Document

class SalesOrder(Document):
    # --- Lifecycle Hooks (called automatically) ---
    
    def before_insert(self):
        """Called before a new document is saved for the first time."""
        self.set_defaults()
    
    def validate(self):
        """Called on every save. Put all business logic validation here."""
        self.validate_items()
        self.calculate_totals()
    
    def before_save(self):
        """After validate, before writing to DB."""
        pass
    
    def on_submit(self):
        """Called when docstatus changes 0→1. Only for submittable docs."""
        self.create_delivery_note()
    
    def on_cancel(self):
        """Called when docstatus changes 1→2."""
        self.cancel_linked_documents()
    
    def on_trash(self):
        """Called just before deletion."""
        pass
    
    def after_insert(self):
        """After first save is complete."""
        frappe.enqueue(
            'my_app.tasks.send_confirmation_email',
            doc_name=self.name,
            queue='short'
        )
    
    # --- Custom Methods ---
    
    def validate_items(self):
        if not self.items:
            frappe.throw("At least one item is required")
        for item in self.items:
            if item.qty <= 0:
                frappe.throw(f"Quantity must be positive for {item.item_code}")
    
    def calculate_totals(self):
        self.total = sum(item.amount for item in self.items)
        self.grand_total = self.total + self.tax_amount
    
    @frappe.whitelist()
    def get_payment_schedule(self):
        """Whitelisted = callable from frontend via frappe.call()"""
        return frappe.get_all(
            'Payment Schedule',
            filters={'parent': self.name},
            fields=['due_date', 'payment_amount']
        )
```

### 4. Form Script Pattern (JavaScript)

```javascript
// my_app/my_module/doctype/sales_order/sales_order.js
frappe.ui.form.on('Sales Order', {
    // Fires when form loads
    onload: function(frm) {
        frm.set_query('customer', function() {
            return { filters: { 'is_active': 1 } };
        });
    },
    
    // Fires when form renders (after data loads)
    refresh: function(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button('Create Invoice', () => {
                frm.call('create_invoice').then(r => {
                    frappe.set_route('Form', 'Sales Invoice', r.message);
                });
            }, 'Create');
        }
    },
    
    // Field-level triggers — named after fieldname
    customer: function(frm) {
        if (frm.doc.customer) {
            frappe.db.get_value('Customer', frm.doc.customer, 
                ['customer_name', 'default_currency'],
                (values) => {
                    frm.set_value('currency', values.default_currency);
                }
            );
        }
    },
    
    // Child table row events
    items_add: function(frm, cdt, cdn) {
        // cdt = child doctype name, cdn = row name
    },
    
    items_remove: function(frm, cdt, cdn) { },
});

// Child table field triggers
frappe.ui.form.on('Sales Order Item', {
    qty: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, 'amount', row.qty * row.rate);
        frm.refresh_field('items');
    }
});
```

---

## Hooks System Overview

`hooks.py` is the integration backbone. Always read `references/hooks-reference.md` for
the full list. Key patterns:

```python
# my_app/hooks.py

app_name = "my_app"
app_title = "My App"

# DocType event hooks — fires Python on document events
doc_events = {
    "Sales Order": {
        "on_submit": "my_app.events.sales_order.on_submit",
        "on_cancel": "my_app.events.sales_order.on_cancel",
    },
    "*": {  # Wildcard — fires for ALL doctypes
        "after_insert": "my_app.events.all_docs.after_insert",
    }
}

# Scheduled jobs
scheduler_events = {
    "daily": ["my_app.tasks.daily_sync"],
    "hourly": ["my_app.tasks.hourly_cleanup"],
    "cron": {
        "0 9 * * 1-5": ["my_app.tasks.weekday_morning_report"]
    }
}

# Override standard Frappe classes
override_doctype_class = {
    "Sales Order": "my_app.overrides.CustomSalesOrder"
}

# Extend standard forms with custom JS
doctype_js = {
    "Sales Order": "public/js/sales_order_extend.js"
}

# Add custom pages
website_route_rules = [
    {"from_route": "/my-portal/<name>", "to_route": "my-portal"}
]

# Extend fixtures (for migration/export)
fixtures = [
    "Custom Field",
    {"dt": "Property Setter", "filters": [["module", "=", "My App"]]},
]
```

---

## Database Operations Cheatsheet

```python
import frappe

# --- frappe.get_doc() — loads full document object ---
doc = frappe.get_doc('Sales Order', 'SAL-ORD-00001')
doc.status = 'Closed'
doc.save()

# --- frappe.get_all() — returns list of dicts ---
orders = frappe.get_all(
    'Sales Order',
    filters={'customer': 'ACME Corp', 'status': ['in', ['Draft', 'Open']]},
    fields=['name', 'grand_total', 'transaction_date'],
    order_by='transaction_date desc',
    limit=50,
    as_list=False  # True returns list of lists
)

# --- frappe.db.get_value() — single field lookup ---
customer_name = frappe.db.get_value('Customer', 'ACME-001', 'customer_name')
# Multiple fields at once
values = frappe.db.get_value('Customer', 'ACME-001', ['customer_name', 'email_id'])

# --- frappe.db.set_value() — update without triggering controller ---
frappe.db.set_value('Sales Order', 'SAL-ORD-00001', 'status', 'Closed')
# Multiple fields
frappe.db.set_value('Sales Order', 'SAL-ORD-00001', {
    'status': 'Closed', 'closed_by': frappe.session.user
})

# --- frappe.db.sql() — raw SQL (use sparingly) ---
results = frappe.db.sql("""
    SELECT so.name, so.grand_total 
    FROM `tabSales Order` so
    WHERE so.company = %(company)s
    AND so.transaction_date >= %(from_date)s
""", values={'company': 'My Company', 'from_date': '2024-01-01'}, as_dict=True)

# --- Query Builder (preferred over raw SQL) ---
from frappe.query_builder import DocType
SO = DocType('Sales Order')
results = (
    frappe.qb.from_(SO)
    .select(SO.name, SO.grand_total, SO.customer)
    .where(SO.status == 'Open')
    .where(SO.grand_total > 10000)
    .orderby(SO.transaction_date, order=frappe.qb.desc)
    .run(as_dict=True)
)

# --- frappe.new_doc() — create without saving ---
new_invoice = frappe.new_doc('Sales Invoice')
new_invoice.customer = 'ACME Corp'
new_invoice.append('items', {
    'item_code': 'ITEM-001',
    'qty': 5,
    'rate': 100
})
new_invoice.insert(ignore_permissions=True)
new_invoice.submit()
frappe.db.commit()  # explicit commit for scripts
```

---

## Background Jobs Pattern

```python
# Enqueue from anywhere
frappe.enqueue(
    'my_app.tasks.process_large_report',
    queue='long',           # short / default / long
    timeout=3600,           # seconds
    job_id='unique-id',     # prevent duplicates
    # kwargs passed to function:
    from_date='2024-01-01',
    to_date='2024-12-31',
)

# tasks.py
def process_large_report(from_date, to_date):
    frappe.publish_progress(0, title='Processing Report')
    # ... do work ...
    frappe.publish_progress(50, title='Processing Report')
    # ... more work ...
    frappe.publish_progress(100, title='Processing Report', description='Done!')
```

---

## REST API & Server Calls

```python
# Expose a Python function to the frontend
@frappe.whitelist()
def get_item_price(item_code, price_list):
    # frappe.session.user is always available
    if not item_code:
        frappe.throw("Item Code is required")
    
    price = frappe.db.get_value('Item Price', 
        {'item_code': item_code, 'price_list': price_list}, 'price_list_rate')
    return price or 0
```

```javascript
// Call from JS
frappe.call({
    method: 'my_app.api.get_item_price',
    args: { item_code: 'ITEM-001', price_list: 'Standard' },
    callback: function(r) {
        console.log(r.message); // return value from Python
    },
    freeze: true,          // show loading overlay
    freeze_message: 'Fetching price...'
});

// Or promise-based
frappe.call('my_app.api.get_item_price', {
    item_code: 'ITEM-001',
    price_list: 'Standard'
}).then(r => {
    if (r.message) {
        frm.set_value('rate', r.message);
    }
});

// REST API (external clients)
// GET: /api/resource/Sales Order/SAL-ORD-00001
// POST: /api/resource/Sales Order
// PUT: /api/resource/Sales Order/SAL-ORD-00001
// DELETE: /api/resource/Sales Order/SAL-ORD-00001
// Custom: /api/method/my_app.api.get_item_price
```

---

## ERPNext Customization Patterns

### Safe Customization (No Core Edits)

```python
# 1. Custom Fields via fixtures — my_app/fixtures/custom_field.json
# OR programmatically in patches/setup:
frappe.get_doc({
    'doctype': 'Custom Field',
    'dt': 'Sales Order',
    'fieldname': 'custom_approval_status',
    'fieldtype': 'Select',
    'options': '\nPending\nApproved\nRejected',
    'label': 'Approval Status',
    'insert_after': 'status',
}).insert(ignore_permissions=True)

# 2. Override controller class in hooks.py
override_doctype_class = {
    "Sales Order": "my_app.overrides.CustomSalesOrder"
}

# 3. Override class itself
# my_app/overrides.py
from erpnext.selling.doctype.sales_order.sales_order import SalesOrder

class CustomSalesOrder(SalesOrder):
    def validate(self):
        super().validate()  # ALWAYS call super
        self.custom_validate()
    
    def custom_validate(self):
        if self.custom_approval_status == 'Rejected':
            frappe.throw("Cannot save a Rejected order")
```

---

## Common Pitfalls & Senior Dev Wisdom

1. **Always call `super()` when overriding ERPNext controller methods** — skipping this breaks
   core logic silently.

2. **Never use `frappe.db.sql()` for reads when `frappe.get_all()` works** — the ORM respects
   permissions; raw SQL bypasses them.

3. **`frappe.db.commit()` in controllers is an anti-pattern** — Frappe manages transactions.
   Only use in standalone scripts or background jobs.

4. **Use `ignore_permissions=True` cautiously** — logs no permission trail. Prefer explicit
   `frappe.has_permission()` checks.

5. **Child table rows**: always use `doc.append('fieldname', {...})` not list append directly.

6. **`frappe.throw()` vs `frappe.msgprint()`** — `throw()` raises an exception and halts;
   `msgprint()` is non-blocking.

7. **Developer mode must be ON** when editing DocTypes so JSON is written to disk (version
   controlled). Never edit in production without migrating.

8. **Never edit `tabDocType` or `tabDocField` directly in SQL** — always use bench migrate.

---

## Decision Framework

When given a Frappe task, follow this decision tree:

```
Is it a schema/model change?
  → Define/modify DocType JSON + controller

Is it business logic on save/submit/cancel?
  → Controller method (validate, on_submit, etc.)

Is it a cross-doctype event listener?
  → hooks.py doc_events

Is it scheduled/async work?
  → scheduler_events + frappe.enqueue()

Is it a UI customization (button, field behavior)?
  → Form script (.js file or Client Script)

Is it an ERPNext standard doctype customization?
  → Custom Field + override_doctype_class, never edit core

Is it a report?
  → Script Report (Python) or Query Report (SQL)

Is it a public-facing page?
  → Portal page (Jinja) or Web Form
```

---

## Loading Additional References

For detailed implementations, read the relevant reference file:

```
references/doctype-patterns.md    → DocType design, naming, child tables, virtual docs
references/python-api.md          → Complete frappe.* Python API reference
references/js-api.md              → Complete frappe.* JS API reference  
references/hooks-reference.md     → All hooks.py keys explained
references/erpnext-customization.md → ERPNext-specific patterns
references/deployment.md          → Bench commands, migrations, production
references/debugging.md           → Debug techniques, logs, profiling
references/testing.md             → Unit tests, UI tests, test fixtures
```

Always load the relevant reference before writing implementation code for complex tasks.
