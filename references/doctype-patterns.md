# DocType Patterns Reference

## Table of Contents
1. [DocType Types](#doctype-types)
2. [Field Types](#field-types)
3. [Naming Strategies](#naming-strategies)
4. [Child Tables](#child-tables)
5. [Single DocTypes](#single-doctypes)
6. [Virtual DocTypes](#virtual-doctypes)
7. [Permissions Model](#permissions-model)
8. [Docstatus Lifecycle](#docstatus-lifecycle)
9. [Actions & Links](#actions--links)

---

## DocType Types

| Type | Use Case | Has Table? | Submittable? |
|------|----------|------------|--------------|
| Standard | Regular entities (Customer, Item) | Yes | Optional |
| Child | Rows in a table field | Yes (child table) | No |
| Single | Singleton config (System Settings) | No own table | No |
| Virtual | External data source, no DB | No | No |
| Tree | Hierarchical (Account, Cost Center) | Yes + lft/rgt | No |

---

## Field Types

```
Data         → Short text (varchar 140)
Small Text   → Text area (varchar 255)  
Text         → Long text (text)
Long Text    → Very long (longtext)
Text Editor  → Rich HTML (longtext)
Markdown Editor → Markdown (longtext)
Code         → Syntax-highlighted code
Int          → Integer
Float        → Float
Currency     → Decimal (precision from system settings)
Percent      → Float shown as %
Date         → Date only
Time         → Time only
Datetime     → Date + time
Duration     → Seconds stored, displayed as 1h 30m
Check        → Boolean (0/1)
Select       → Dropdown from Options (newline-separated)
Link         → FK to another DocType
Dynamic Link → FK where doctype itself is a field
Table        → Child table
Table MultiSelect → Multi-select from child table
Attach       → File attachment URL
Attach Image → Image attachment URL
Password     → Encrypted storage
Color        → Color picker
Geolocation  → GeoJSON
Rating       → Star rating (0-5)
Signature    → Image signature pad
HTML         → Static HTML display
HTML Editor  → Inline HTML
Heading      → Section label (no data)
Column Break → Layout column break
Section Break → Section separator with optional label
Tab Break    → Tab navigation break
```

---

## Naming Strategies

```json
// In DocType JSON — autoname field:

// 1. Series (most common) — generates PREF-YYYY-#####
"autoname": "SLO-ORD-.YYYY.-.#####"

// 2. Field value as name
"autoname": "field:email_id"

// 3. Hash (UUID-like)
"autoname": "hash"

// 4. Prompt (user enters manually)
"autoname": "prompt"

// 5. Custom — override in controller
"autoname": "naming_series:"  // uses Naming Series field

// Custom naming in controller:
class MyDoc(Document):
    def autoname(self):
        self.name = f"CUSTOM-{self.some_field}-{frappe.utils.nowdate()}"
```

---

## Child Tables

```python
# Define child doctype: My App Item
# In parent doctype, add a Table field pointing to child doctype

# Adding rows:
doc = frappe.get_doc('My Parent', 'PARENT-001')
doc.append('items', {
    'item_code': 'ITEM-001',
    'qty': 10,
    'rate': 50.0,
    'amount': 500.0
})
doc.save()

# Iterating:
for item in doc.items:
    print(item.item_code, item.qty)

# Finding a row:
row = next((i for i in doc.items if i.item_code == 'ITEM-001'), None)

# Removing rows:
doc.items = [i for i in doc.items if i.item_code != 'TO-REMOVE']
doc.save()

# Setting value on child row from JS:
frappe.model.set_value(cdt, cdn, 'amount', qty * rate);
frappe.model.get_value(cdt, cdn, 'qty');
locals[cdt][cdn]  // direct row access
```

---

## Single DocTypes

```python
# Reading a Single DocType:
settings = frappe.get_single('My App Settings')
print(settings.api_key)

# Or using get_value:
api_key = frappe.db.get_single_value('My App Settings', 'api_key')

# Saving a Single DocType:
settings = frappe.get_single('My App Settings')
settings.api_key = 'new-key'
settings.save()

# In JS:
frappe.db.get_single_value('My App Settings', 'api_key')
    .then(value => console.log(value));
```

---

## Virtual DocTypes

```python
# Virtual DocType — reads from external source, no DB table
# Set is_virtual = 1 in DocType

class ExternalOrderDoc(Document):
    @staticmethod
    def get_list(args):
        """Called for list view — return list of dicts"""
        api = ExternalAPI()
        return api.fetch_orders(
            limit=args.get('page_length', 20),
            start=args.get('start', 0)
        )
    
    @staticmethod
    def get_count(args):
        return ExternalAPI().count_orders()
    
    @staticmethod
    def get_stats(args):
        return {}
    
    def db_insert(self, *args, **kwargs):
        ExternalAPI().create_order(self.as_dict())
    
    def load_from_db(self):
        data = ExternalAPI().get_order(self.name)
        super(Document, self).__init__(data)
    
    def db_update(self, *args, **kwargs):
        ExternalAPI().update_order(self.name, self.as_dict())
    
    def delete(self):
        ExternalAPI().delete_order(self.name)
```

---

## Permissions Model

```
Permission Levels (perm_level):
  0  → Document level (Read/Write/Create/Delete/Submit/Cancel/Amend/Report/Import/Export/Print/Email/Share)
  1+ → Field level (restrict specific fields to certain roles)

Permission Types:
  Read     → Can view documents
  Write    → Can edit (requires Read)
  Create   → Can create new documents
  Delete   → Can delete (requires Write)
  Submit   → Can change docstatus 0→1
  Cancel   → Can change docstatus 1→2
  Amend    → Can create amended copy of cancelled doc
  Report   → Can view in reports
  Import   → Can bulk import via Data Import
  Export   → Can export to CSV/Excel
  Print    → Can print
  Email    → Can email document
  Share    → Can share with other users
```

```python
# Check permission in code:
frappe.has_permission('Sales Order', 'write', doc=self)
frappe.has_permission('Sales Order', 'submit')
frappe.only_if_user_is_logged_in()

# Get permitted documents (respects permissions):
frappe.get_list('Sales Order', filters={'status': 'Open'})
# vs all docs (bypasses permissions — use carefully):
frappe.get_all('Sales Order', filters={'status': 'Open'}, ignore_permissions=True)
```

---

## Docstatus Lifecycle

```
docstatus = 0  →  Draft    (default, editable)
docstatus = 1  →  Submitted (locked, triggers on_submit)
docstatus = 2  →  Cancelled (final, triggers on_cancel)

Controller hooks by lifecycle:
  before_insert → validate → before_save → after_insert → after_save
  → [before_submit → on_submit → after_submit]
  → [before_cancel → on_cancel → after_cancel]
  → [on_trash]

In JSON: "is_submittable": 1 to enable submit/cancel
```

---

## Actions & Links

```json
// In DocType JSON:
"links": [
    {
        "link_doctype": "Sales Invoice",
        "link_fieldname": "sales_order",
        "label": "Sales Invoice"
    }
],
"actions": [
    {
        "action_label": "Send Reminder",
        "action_type": "Server Action",
        "action": "my_app.actions.send_reminder"
    }
]
```

```python
# Programmatic button in controller
def get_dashboard_data(data):
    # Override get_dashboard_data for dashboard transactions
    return data
```
