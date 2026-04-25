#!/usr/bin/env python3
"""
Frappe App Boilerplate Generator
Usage: python generate_boilerplate.py <app_name> <module_name> <doctype_name>
"""

import os
import sys
import json

def snake_case(name):
    return name.lower().replace(' ', '_')

def pascal_case(name):
    return ''.join(word.capitalize() for word in name.replace('_', ' ').split())

def generate_app(app_name, module_name, doctype_name):
    app = snake_case(app_name)
    module = snake_case(module_name)
    doctype = snake_case(doctype_name)
    DocType = pascal_case(doctype_name)

    structure = {
        f"{app}/__init__.py": f'__version__ = "0.0.1"\n',
        
        f"{app}/hooks.py": f'''app_name = "{app}"
app_title = "{app_name}"
app_publisher = "My Company"
app_description = "{app_name} Application"
app_version = "0.0.1"
app_email = "dev@mycompany.com"
app_license = "MIT"

# DocType Events
doc_events = {{
    # "{DocType}": {{
    #     "on_submit": "{app}.events.{doctype}.on_submit",
    # }}
}}

# Scheduled Jobs
scheduler_events = {{
    "daily": [
        # "{app}.tasks.daily_cleanup"
    ],
}}

# Controller Overrides
# override_doctype_class = {{
#     "Sales Order": "{app}.overrides.CustomSalesOrder"
# }}

# Frontend Assets
# doctype_js = {{
#     "Sales Order": "public/js/sales_order_extend.js"
# }}

# Fixtures
fixtures = [
    {{"dt": "Custom Field", "filters": [["module", "=", "{app_name}"]]}},
    {{"dt": "Property Setter", "filters": [["module", "=", "{app_name}"]]}},
]
''',

        f"{app}/modules.txt": f"{module_name}\n",
        
        f"{app}/patches.txt": f"# Add patches here (one per line)\n# {app}.patches.v0_0.example_patch\n",
        
        f"{app}/{module}/__init__.py": "",
        
        f"{app}/{module}/doctype/__init__.py": "",
        
        f"{app}/{module}/doctype/{doctype}/__init__.py": "",
        
        f"{app}/{module}/doctype/{doctype}/{doctype}.py": f'''import frappe
from frappe.model.document import Document
from frappe import _


class {DocType}(Document):
    # --- Lifecycle Hooks ---

    def before_insert(self):
        pass

    def validate(self):
        self._validate_required_fields()

    def on_submit(self):
        pass

    def on_cancel(self):
        pass

    def on_trash(self):
        pass

    # --- Private Validators ---

    def _validate_required_fields(self):
        """Add your validation logic here"""
        pass

    # --- Whitelisted Methods (callable from JS) ---

    @frappe.whitelist()
    def my_action(self):
        """Example whitelisted method"""
        frappe.has_permission(self.doctype, "write", doc=self, throw=True)
        return {{"status": "success", "message": _("Action completed")}}
''',

        f"{app}/{module}/doctype/{doctype}/{doctype}.js": f'''// Copyright (c) {{year}}, My Company and contributors
// For license information, please see license.txt

frappe.ui.form.on('{doctype_name}', {{
    // --- Lifecycle Events ---

    setup: function(frm) {{
        // Set up queries, etc.
    }},

    onload: function(frm) {{
        // Runs when form data loads
    }},

    refresh: function(frm) {{
        // Runs on every refresh
        if (frm.doc.docstatus === 1) {{
            // Add buttons for submitted docs
            frm.add_custom_button(__('My Action'), function() {{
                frappe.confirm(
                    __('Are you sure?'),
                    () => {{
                        frm.call('my_action').then(r => {{
                            if (r.message.status === 'success') {{
                                frappe.show_alert({{
                                    message: r.message.message,
                                    indicator: 'green'
                                }});
                                frm.reload_doc();
                            }}
                        }});
                    }}
                );
            }}, __('Actions'));
        }}
    }},

    // --- Field Events (named after fieldname) ---
    // example_field: function(frm) {{
    //     // Handle field change
    // }},
}});
''',

        f"{app}/{module}/doctype/{doctype}/{doctype}.json": json.dumps({
            "actions": [],
            "allow_rename": 1,
            "autoname": "naming_series:",
            "creation": "2024-01-01 00:00:00.000000",
            "doctype": "DocType",
            "document_type": "Document",
            "editable_grid": 1,
            "engine": "InnoDB",
            "field_order": [
                "naming_series",
                "title",
                "status",
                "column_break_1",
                "company",
                "section_break_details",
                "description",
                "amended_from"
            ],
            "fields": [
                {"fieldname": "naming_series", "fieldtype": "Select", "label": "Series",
                 "options": f"{doctype_name.upper()[:4]}-.YYYY.-", "set_only_once": 1},
                {"fieldname": "title", "fieldtype": "Data", "in_list_view": 1,
                 "label": "Title", "reqd": 1},
                {"fieldname": "status", "fieldtype": "Select", "in_list_view": 1,
                 "label": "Status", "options": "Draft\nOpen\nClosed\nCancelled",
                 "default": "Draft"},
                {"fieldname": "column_break_1", "fieldtype": "Column Break"},
                {"fieldname": "company", "fieldtype": "Link", "label": "Company",
                 "options": "Company"},
                {"fieldname": "section_break_details", "fieldtype": "Section Break",
                 "label": "Details"},
                {"fieldname": "description", "fieldtype": "Text Editor",
                 "label": "Description"},
                {"fieldname": "amended_from", "fieldtype": "Link", "label": "Amended From",
                 "no_copy": 1, "options": doctype_name, "print_hide": 1, "read_only": 1}
            ],
            "is_submittable": 1,
            "links": [],
            "modified": "2024-01-01 00:00:00.000000",
            "modified_by": "Administrator",
            "module": module_name,
            "name": doctype_name,
            "naming_rule": "By \"Naming Series\" field",
            "owner": "Administrator",
            "permissions": [
                {"create": 1, "delete": 1, "email": 1, "export": 1, "print": 1,
                 "read": 1, "report": 1, "role": "System Manager", "share": 1,
                 "submit": 1, "cancel": 1, "amend": 1, "write": 1}
            ],
            "sort_field": "modified",
            "sort_order": "DESC",
            "states": [],
            "track_changes": 1,
        }, indent=2),

        f"{app}/{module}/doctype/{doctype}/test_{doctype}.py": f'''import frappe
import unittest
from frappe.tests.utils import FrappeTestCase


class Test{DocType}(FrappeTestCase):
    """Tests for {DocType}"""

    def setUp(self):
        """Set up test fixtures"""
        pass

    def tearDown(self):
        """Clean up after tests"""
        frappe.db.rollback()

    def test_basic_creation(self):
        """Test that a basic {DocType} can be created"""
        doc = frappe.get_doc({{
            "doctype": "{doctype_name}",
            "title": "_Test {doctype_name}",
        }}).insert(ignore_permissions=True)

        self.assertEqual(doc.doctype, "{doctype_name}")
        self.assertEqual(doc.title, "_Test {doctype_name}")

    def test_validation(self):
        """Test validation rules"""
        doc = frappe.new_doc("{doctype_name}")
        # Test that missing required fields raise error
        with self.assertRaises(frappe.MandatoryError):
            doc.insert()
''',

        f"{app}/api/__init__.py": "",
        
        f"{app}/api.py": f'''"""
Public API endpoints for {app_name}
All functions decorated with @frappe.whitelist() are accessible via:
/api/method/{app}.api.<function_name>
"""
import frappe
from frappe import _


@frappe.whitelist()
def get_status_summary():
    """
    Get a summary of document statuses.
    Accessible at: /api/method/{app}.api.get_status_summary
    """
    frappe.has_permission("{doctype_name}", "read", throw=True)
    
    return frappe.db.sql("""
        SELECT status, COUNT(*) as count
        FROM `tab{doctype_name}`
        WHERE docstatus < 2
        GROUP BY status
    """, as_dict=True)
''',

        f"{app}/tasks.py": f'''"""
Scheduled background tasks for {app_name}
Configure in hooks.py under scheduler_events
"""
import frappe


def daily_cleanup():
    """
    Daily cleanup task.
    Add to hooks.py: scheduler_events = {{"daily": ["{app}.tasks.daily_cleanup"]}}
    """
    frappe.logger().info("Running daily cleanup for {app_name}")
    # Your cleanup logic here
''',

        f"setup.py": f'''from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\\n")

setup(
    name="{app}",
    version="0.0.1",
    description="{app_name}",
    author="My Company",
    author_email="dev@mycompany.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
''',
        "requirements.txt": "frappe\n",
        ".gitignore": "*.pyc\n__pycache__\n*.egg-info\ndist\nbuild\n.env\n",
    }

    for filepath, content in structure.items():
        dirpath = os.path.dirname(filepath)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Created: {filepath}")

    print(f"\n✅ App '{app}' generated successfully!")
    print(f"\nNext steps:")
    print(f"  1. cd frappe-bench")
    print(f"  2. cp -r /path/to/{app} apps/")
    print(f"  3. bench get-app {app}  # or pip install -e apps/{app}")
    print(f"  4. bench --site mysite.localhost install-app {app}")
    print(f"  5. bench --site mysite.localhost migrate")


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python generate_boilerplate.py <app_name> <module_name> <doctype_name>")
        print("Example: python generate_boilerplate.py 'My App' 'My Module' 'My DocType'")
        sys.exit(1)
    
    generate_app(sys.argv[1], sys.argv[2], sys.argv[3])
