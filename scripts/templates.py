#!/usr/bin/env python3
"""
Frappe Code Template Generator
Quick scaffolding for common Frappe patterns.
Usage: python templates.py <template_name> [options]
"""

TEMPLATES = {

"controller": '''import frappe
from frappe.model.document import Document
from frappe import _


class {ClassName}(Document):
    """
    Controller for {DocTypeName} DocType.
    """

    def before_insert(self):
        self._set_defaults()

    def validate(self):
        self._validate_{fieldname}()
        self._calculate_totals()

    def on_submit(self):
        self._create_linked_documents()

    def on_cancel(self):
        self._cancel_linked_documents()

    def _set_defaults(self):
        if not self.date:
            self.date = frappe.utils.today()

    def _validate_{fieldname}(self):
        if not self.{fieldname}:
            frappe.throw(_("{FieldLabel} is required"), title=_("Missing Required Field"))

    def _calculate_totals(self):
        self.total = sum(flt(item.amount) for item in self.items)

    def _create_linked_documents(self):
        pass

    def _cancel_linked_documents(self):
        pass

    @frappe.whitelist()
    def get_summary(self):
        """Returns document summary — callable from JS via frm.call('get_summary')"""
        return {
            "name": self.name,
            "status": self.status,
            "total": self.total,
        }
''',

"form_script": '''// {DocTypeName} Form Script
// Extends the standard form behavior

frappe.ui.form.on('{DocTypeName}', {
    /**
     * Setup — runs once when form class is created
     * Use for: setting queries, initializing event handlers
     */
    setup: function(frm) {
        // Set filter on Link field
        frm.set_query('{link_fieldname}', function() {
            return {
                filters: {
                    'is_active': 1
                }
            };
        });
    },

    /**
     * Refresh — runs every time form is rendered
     * Use for: conditional buttons, indicators
     */
    refresh: function(frm) {
        // Add submit action button
        if (frm.doc.docstatus === 1 && frappe.user.has_role('Manager')) {
            frm.add_custom_button(__('Close'), function() {
                frappe.confirm(
                    __('Close this {DocTypeName}?'),
                    function() {
                        frm.call('close_document').then(r => {
                            frm.reload_doc();
                        });
                    }
                );
            }, __('Actions'));
        }

        // Set visual indicator
        const colors = {
            'Open': 'blue', 'Closed': 'green', 'Cancelled': 'red'
        };
        frm.set_df_property(
            'status', 'options',
            Object.keys(colors).join('\\n')
        );
    },

    /**
     * Field trigger — named after fieldname
     */
    {fieldname}: function(frm) {
        if (frm.doc.{fieldname}) {
            frappe.db.get_value('{LinkedDocType}', frm.doc.{fieldname}, 
                ['field1', 'field2'],
                function(values) {
                    frm.set_value('mapped_field', values.field1);
                }
            );
        }
    },
});

// Child table field triggers
frappe.ui.form.on('{ChildDocType}', {
    qty: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, 'amount', row.qty * row.rate);
        frm.refresh_field('items');
        frm.set_value('total', frm.doc.items.reduce((sum, i) => sum + (i.amount || 0), 0));
    },

    items_add: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        // Set default values on new row
        frappe.model.set_value(cdt, cdn, 'date', frappe.datetime.nowdate());
    },
});
''',

"background_job": '''"""
Background job for {operation_name}.
Enqueue from controller or API:
    frappe.enqueue('{app}.jobs.{job_module}.{function_name}', queue='long', ...)
"""
import frappe


def {function_name}(filters=None, notify_user=None):
    """
    Long-running background task.
    
    Args:
        filters: dict of query filters
        notify_user: email address to notify on completion
    """
    frappe.publish_progress(0, title='{operation_name}', description='Starting...')
    
    try:
        records = frappe.get_all(
            '{DocType}',
            filters=filters or {},
            fields=['name'],
            limit=None
        )
        
        total = len(records)
        processed = 0
        errors = []
        
        for record in records:
            try:
                _process_single_record(record.name)
                processed += 1
            except Exception as e:
                errors.append({'name': record.name, 'error': str(e)})
                frappe.log_error(f"Error in {function_name}", frappe.get_traceback())
            
            progress = int((processed / total) * 100) if total else 100
            frappe.publish_progress(
                progress,
                title='{operation_name}',
                description=f"Processed {{processed}}/{{total}}"
            )
        
        result_message = (
            f"Completed: {{processed}} records processed, {{len(errors)}} errors."
        )
        
        frappe.publish_progress(100, title='{operation_name}', description=result_message)
        
        if notify_user:
            frappe.sendmail(
                recipients=[notify_user],
                subject='{operation_name} Complete',
                message=f"<p>{{result_message}}</p>"
            )
        
        return {'processed': processed, 'errors': errors}
    
    except Exception:
        frappe.publish_progress(100, title='{operation_name}', description='Failed!')
        frappe.log_error('{operation_name} Failed', frappe.get_traceback())
        raise


def _process_single_record(name):
    doc = frappe.get_doc('{DocType}', name)
    # Process logic here
    doc.save(ignore_permissions=True)
    frappe.db.commit()
''',

"api_endpoint": '''"""
REST API endpoints for {module_name}.
Access via: /api/method/{app}.{module}.api.{function_name}
"""
import frappe
from frappe import _
from frappe.utils import cint, flt


@frappe.whitelist()
def get_{resource}_list(
    page_size=20,
    page=1,
    search=None,
    status=None,
):
    """
    List {resource}s with pagination and search.
    
    GET /api/method/{app}.{module}.api.get_{resource}_list
    Params: page_size, page, search, status
    """
    page_size = cint(page_size) or 20
    page = cint(page) or 1
    
    filters = {{"docstatus": ["<", 2]}}
    if status:
        filters["status"] = status
    
    if search:
        # Full-text style search
        filters["name"] = ["like", f"%{{search}}%"]
    
    items = frappe.get_all(
        "{ResourceDocType}",
        filters=filters,
        fields=["name", "title", "status", "creation"],
        order_by="modified desc",
        limit_page_length=page_size,
        limit_start=(page - 1) * page_size,
    )
    
    total = frappe.db.count("{ResourceDocType}", filters=filters)
    
    return {{
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": -(-total // page_size),  # ceiling division
    }}


@frappe.whitelist()
def get_{resource}(name):
    """
    Get single {resource} detail.
    GET /api/method/{app}.{module}.api.get_{resource}?name=DOC-001
    """
    frappe.has_permission("{ResourceDocType}", "read", throw=True)
    
    doc = frappe.get_doc("{ResourceDocType}", name)
    return doc.as_dict()


@frappe.whitelist(methods=["POST"])
def create_{resource}(data):
    """
    Create a new {resource}.
    POST /api/method/{app}.{module}.api.create_{resource}
    Body: {{"data": {{...fields...}}}}
    """
    import json
    if isinstance(data, str):
        data = json.loads(data)
    
    doc = frappe.new_doc("{ResourceDocType}")
    doc.update(data)
    doc.insert(ignore_permissions=False)
    
    return {{"name": doc.name, "message": _("{ResourceDocType} created successfully")}}
''',

"patch": '''"""
Migration Patch: {description}
File: {app}/patches/{version}/{patch_name}.py
Add to patches.txt: {app}.patches.{version}.{patch_name}

IMPORTANT:
- Patches run exactly once per site via bench migrate
- Must be IDEMPOTENT — safe to run multiple times
- Use frappe.flags.in_patch to detect patch context
- Always commit at end if you made data changes
"""
import frappe


def execute():
    """
    {description}
    """
    frappe.logger().info("Running patch: {patch_name}")
    
    # --- Schema changes (usually not needed, use Custom Fields) ---
    # if not frappe.db.has_column("My DocType", "my_field"):
    #     frappe.db.add_column("My DocType", "my_field", "varchar(140)")
    
    # --- Data migration ---
    affected = frappe.db.sql("""
        SELECT name FROM `tabMy DocType`
        WHERE old_field IS NOT NULL
        AND new_field IS NULL
    """, as_dict=True)
    
    if not affected:
        frappe.logger().info("Patch {patch_name}: No records to migrate")
        return
    
    frappe.logger().info(f"Migrating {{len(affected)}} records...")
    
    for row in affected:
        try:
            frappe.db.set_value("My DocType", row.name, {{
                "new_field": frappe.db.get_value("My DocType", row.name, "old_field"),
            }}, update_modified=False)
        except Exception:
            frappe.log_error(f"Patch error on {{row.name}}", frappe.get_traceback())
    
    frappe.db.commit()
    frappe.logger().info(f"Patch {patch_name}: Complete")
''',

"permission_query": '''"""
Row-level permission query for {DocType}.
Registered in hooks.py:
    permission_query_conditions = {{
        "{DocType}": "{app}.permissions.get_{doctype}_conditions"
    }}
"""
import frappe


def get_{doctype}_conditions(user=None):
    """
    Returns WHERE clause to filter {DocType} records by user access.
    This runs on EVERY list/report query — must be fast!
    """
    if not user:
        user = frappe.session.user
    
    # Admins see everything
    if "System Manager" in frappe.get_roles(user):
        return ""
    
    # Sales managers see all their team's orders
    if "Sales Manager" in frappe.get_roles(user):
        team_members = frappe.db.get_all(
            "User",
            filters={{"reports_to": user}},
            pluck="name"
        )
        team_members.append(user)
        members_str = "', '".join(team_members)
        return f"`tab{DocType}`.owner IN ('{{members_str}}')"
    
    # Regular users see only their own
    return f"`tab{DocType}`.owner = '{{user}}'"


def has_{doctype}_permission(doc, user=None, ptype="read"):
    """
    Document-level permission check.
    Registered in hooks.py:
        has_permission = {{
            "{DocType}": "{app}.permissions.has_{doctype}_permission"
        }}
    Returns True/False or None (to use default)
    """
    if not user:
        user = frappe.session.user
    
    if "System Manager" in frappe.get_roles(user):
        return True
    
    # Owner always has access
    if doc.owner == user:
        return True
    
    # Assigned users have access
    if frappe.db.exists("ToDo", {{
        "reference_type": "{DocType}",
        "reference_name": doc.name,
        "owner": user,
        "status": "Open"
    }}):
        return True
    
    return False
''',
}

if __name__ == '__main__':
    print("Available templates:")
    for name in TEMPLATES:
        print(f"  - {name}")
    print("\nUse this file as a reference for template content.")
    print("Templates contain {Placeholder} values to be replaced for each use case.")
