# ERPNext Customization Reference

## Golden Rules for ERPNext Customization

1. **Never edit core ERPNext/Frappe files** — updates will overwrite your changes.
2. **Always use Custom Fields**, not modifying standard DocType JSON.
3. **Always call `super()`** when overriding methods.
4. **Use fixtures** to make customizations portable across environments.
5. **Prefix everything** with your app name to avoid conflicts.

---

## Custom Fields

### Via UI (Customization → Custom Field)
Best for one-off fields. Export to fixtures for portability.

### Via Code (in patches or setup scripts)
```python
import frappe

def add_custom_fields():
    custom_fields = {
        'Sales Order': [
            {
                'fieldname': 'custom_approval_required',
                'fieldtype': 'Check',
                'label': 'Approval Required',
                'insert_after': 'status',
                'default': '0',
                'in_list_view': 0,
            },
            {
                'fieldname': 'custom_approved_by',
                'fieldtype': 'Link',
                'options': 'User',
                'label': 'Approved By',
                'insert_after': 'custom_approval_required',
                'depends_on': 'eval:doc.custom_approval_required == 1',
                'read_only': 1,
            },
        ],
        'Customer': [
            {
                'fieldname': 'custom_customer_tier',
                'fieldtype': 'Select',
                'label': 'Customer Tier',
                'options': '\nBronze\nSilver\nGold\nPlatinum',
                'insert_after': 'customer_group',
            }
        ]
    }
    
    create_custom_fields(custom_fields)

def create_custom_fields(custom_fields):
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    create_custom_fields(custom_fields, ignore_validate=frappe.flags.in_patch)
```

---

## Property Setters

Override standard field properties without Custom Fields:

```python
# Make a standard field mandatory
frappe.make_property_setter({
    'doctype': 'Sales Order',
    'fieldname': 'po_no',
    'property': 'reqd',
    'value': '1',
    'property_type': 'Check'
})

# Hide a standard field
frappe.make_property_setter({
    'doctype': 'Sales Invoice',
    'fieldname': 'debit_to',
    'property': 'hidden',
    'value': '1',
    'property_type': 'Check'
})

# Change options of a Select field
frappe.make_property_setter({
    'doctype': 'Lead',
    'fieldname': 'status',
    'property': 'options',
    'value': 'New\nContacted\nQualified\nConverted\nLost',
    'property_type': 'Text'
})
```

---

## Controller Override Pattern

```python
# hooks.py
override_doctype_class = {
    "Sales Order": "my_app.overrides.sales_order.CustomSalesOrder"
}

# my_app/overrides/sales_order.py
import frappe
from erpnext.selling.doctype.sales_order.sales_order import SalesOrder

class CustomSalesOrder(SalesOrder):
    
    def validate(self):
        """ALWAYS call super first unless intentionally skipping"""
        super().validate()
        self.custom_validate_approval()
    
    def on_submit(self):
        super().on_submit()
        self.notify_approver()
    
    def custom_validate_approval(self):
        if self.custom_approval_required and not self.custom_approved_by:
            frappe.throw(
                "This order requires approval before saving. "
                "Please get it approved by a manager.",
                title="Approval Required"
            )
    
    def notify_approver(self):
        if not self.custom_approval_required:
            return
        frappe.sendmail(
            recipients=[self.custom_approved_by],
            subject=f"Sales Order {self.name} Submitted",
            message=frappe.render_template(
                'my_app/templates/emails/so_submitted.html',
                {'doc': self}
            ),
            reference_doctype=self.doctype,
            reference_name=self.name
        )
    
    @frappe.whitelist()
    def approve_order(self):
        """Called from form button"""
        frappe.has_permission(self.doctype, 'write', doc=self, throw=True)
        if not frappe.has_role('Sales Manager'):
            frappe.throw("Only Sales Managers can approve orders")
        
        self.db_set('custom_approved_by', frappe.session.user)
        self.notify_submitter()
        return 'approved'
```

---

## Extending Form Scripts

```javascript
// public/js/sales_order_extend.js
// Listed in hooks.py under doctype_js

// IMPORTANT: This runs alongside, not replacing, standard scripts
frappe.ui.form.on('Sales Order', {
    refresh: function(frm) {
        // Add approval button
        if (frm.doc.custom_approval_required && 
            !frm.doc.custom_approved_by && 
            frm.doc.docstatus === 0) {
            frm.add_custom_button('Approve Order', function() {
                frappe.confirm(
                    'Are you sure you want to approve this order?',
                    () => {
                        frm.call('approve_order').then(r => {
                            if (r.message === 'approved') {
                                frappe.show_alert({
                                    message: 'Order Approved',
                                    indicator: 'green'
                                });
                                frm.reload_doc();
                            }
                        });
                    }
                );
            }, 'Actions');
        }
        
        // Show approval status indicator
        if (frm.doc.custom_approval_required) {
            if (frm.doc.custom_approved_by) {
                frm.set_indicator_formatter('custom_approved_by', () => 'green');
            } else {
                frm.dashboard.set_headline(
                    `<span class="indicator red">Pending Approval</span>`
                );
            }
        }
    },
    
    custom_approval_required: function(frm) {
        frm.toggle_reqd('custom_approved_by', frm.doc.custom_approval_required);
    }
});
```

---

## Workspace Customization

```python
# Add your app's workspace programmatically in setup
def setup_workspace():
    if not frappe.db.exists('Workspace', 'My App'):
        frappe.get_doc({
            'doctype': 'Workspace',
            'name': 'My App',
            'module': 'My App',
            'label': 'My App',
            'icon': 'briefcase',
            'type': 'module',
            'content': '[]',
            'links': [
                {
                    'type': 'DocType',
                    'label': 'My DocType',
                    'name': 'My DocType',
                    'onboard': 1,
                }
            ]
        }).insert(ignore_permissions=True)
```

---

## Report Patterns

### Script Report (Python)
```python
# my_app/report/sales_summary/sales_summary.py

def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    return columns, data, None, chart

def get_columns():
    return [
        {'label': 'Order', 'fieldname': 'name', 'fieldtype': 'Link', 
         'options': 'Sales Order', 'width': 150},
        {'label': 'Customer', 'fieldname': 'customer', 'fieldtype': 'Link', 
         'options': 'Customer', 'width': 200},
        {'label': 'Amount', 'fieldname': 'grand_total', 'fieldtype': 'Currency', 
         'width': 120},
    ]

def get_data(filters):
    conditions = []
    if filters.get('from_date'):
        conditions.append(f"transaction_date >= %(from_date)s")
    
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    
    return frappe.db.sql(f"""
        SELECT name, customer, grand_total, transaction_date
        FROM `tabSales Order`
        WHERE docstatus = 1
        {where}
        ORDER BY transaction_date DESC
    """, filters, as_dict=True)

def get_chart(data):
    return {
        'type': 'bar',
        'data': {
            'labels': [d.customer for d in data[:10]],
            'datasets': [{'values': [d.grand_total for d in data[:10]]}]
        }
    }
```

### Script Report Filters (JSON)
```json
[
    {
        "fieldname": "from_date",
        "label": "From Date",
        "fieldtype": "Date",
        "default": "Today",
        "reqd": 1
    },
    {
        "fieldname": "company",
        "label": "Company",
        "fieldtype": "Link",
        "options": "Company",
        "default": ""
    }
]
```

---

## Web Forms (Customer Portal)

```python
# Web Form created via UI or JSON
# my_app/web_form/customer_request/customer_request.py

def get_context(context):
    """Add extra context for Jinja rendering"""
    context.title = "Submit a Request"

def validate(doc, method):
    """Validate before save — same as controller validate"""
    if not doc.description:
        frappe.throw("Please provide a description")

def on_payment_authorized(payment_status):
    """Called after payment for paid web forms"""
    pass
```

---

## Notifications (Automated Email/SMS)

```python
# Via Notification DocType (recommended) or programmatically:
def setup_notifications():
    frappe.get_doc({
        'doctype': 'Notification',
        'name': 'Sales Order Approval Reminder',
        'subject': 'Sales Order {{ doc.name }} needs approval',
        'document_type': 'Sales Order',
        'event': 'Days After',
        'days_after_or_before': 2,
        'date_changed': 'transaction_date',
        'enabled': 1,
        'send_to_all_assignees': 0,
        'recipients': [{'receiver_by_role': 'Sales Manager'}],
        'message': '<p>Please approve Sales Order {{ doc.name }}</p>',
        'condition': 'doc.custom_approval_required and not doc.custom_approved_by',
    }).insert(ignore_permissions=True)
```

---

## Patches (Database Migrations)

```python
# Add to patches.txt: my_app.patches.v1_1.add_approval_field
# my_app/patches/v1_1/add_approval_field.py

import frappe

def execute():
    """
    Migration patch — runs exactly once via bench migrate.
    Must be idempotent — check before acting.
    """
    if not frappe.db.has_column('Sales Order', 'custom_approval_required'):
        # Normally handled by Custom Field, but if schema migration needed:
        frappe.db.add_column('Sales Order', 'custom_approval_required', 'tinyint(1) default 0')
    
    # Data migration
    frappe.db.sql("""
        UPDATE `tabSales Order`
        SET custom_approval_required = 1
        WHERE grand_total > 100000
        AND docstatus = 0
    """)
    
    frappe.db.commit()
```

---

## Exporting Customizations to App

```bash
# Export current customizations from the UI to your app's fixtures
bench --site mysite.localhost export-fixtures --app my_app

# This creates JSON files in my_app/fixtures/
# Commit these to git and they'll be installed on bench migrate
```
