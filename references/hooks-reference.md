# Hooks Reference (hooks.py)

All keys available in `hooks.py` with descriptions and examples.

## App Identity
```python
app_name = "my_app"
app_title = "My App"
app_publisher = "My Company"
app_description = "App description"
app_version = "1.0.0"
app_icon = "octicon octicon-file-directory"
app_color = "#589494"
app_email = "dev@mycompany.com"
app_license = "MIT"
```

## DocType Events
```python
# Trigger Python on standard DocType events
doc_events = {
    "Sales Order": {
        "validate": "my_app.events.sales_order.validate",
        "on_submit": "my_app.events.sales_order.on_submit",
        "on_cancel": "my_app.events.sales_order.on_cancel",
        "on_trash": "my_app.events.sales_order.on_trash",
        "after_insert": "my_app.events.sales_order.after_insert",
        "before_save": "my_app.events.sales_order.before_save",
        "after_save": "my_app.events.sales_order.after_save",
    },
    "*": {  # All doctypes
        "after_insert": "my_app.events.all.after_insert",
    }
}
```

## Scheduled Jobs
```python
scheduler_events = {
    # Run at specific intervals
    "all": ["my_app.tasks.run_every_heartbeat"],        # ~5 min
    "hourly": ["my_app.tasks.hourly_task"],
    "daily": ["my_app.tasks.daily_cleanup"],
    "weekly": ["my_app.tasks.weekly_report"],
    "monthly": ["my_app.tasks.monthly_billing"],
    
    # Interval-based
    "hourly_long": ["my_app.tasks.heavy_hourly"],       # Long queue
    "daily_long": ["my_app.tasks.heavy_daily"],
    "weekly_long": ["my_app.tasks.heavy_weekly"],
    "monthly_long": ["my_app.tasks.heavy_monthly"],
    
    # Cron syntax
    "cron": {
        "0 9 * * 1-5": ["my_app.tasks.weekday_9am"],   # Weekdays at 9am
        "*/30 * * * *": ["my_app.tasks.every_30_min"],  # Every 30 min
    }
}
```

## Class Overrides
```python
# Replace standard DocType controller with custom class
override_doctype_class = {
    "Sales Order": "my_app.overrides.CustomSalesOrder",
    "Purchase Order": "my_app.overrides.CustomPurchaseOrder",
}

# Override Whitelisted methods (monkey-patch)
override_whitelisted_methods = {
    "frappe.client.get_count": "my_app.overrides.custom_get_count",
}
```

## Frontend Assets
```python
# Extra JS loaded on specific DocType forms
doctype_js = {
    "Sales Order": "public/js/sales_order_extend.js",
    "Customer": ["public/js/customer_extend.js", "public/js/crm_utils.js"],
}

# Extra CSS for specific DocType forms
doctype_css = {
    "Sales Order": "public/css/sales_order.css",
}

# Extra JS on list views
doctype_list_js = {
    "Sales Order": "public/js/sales_order_list.js",
}

# Extra JS on calendar views
doctype_calendar_js = {
    "Sales Order": "public/js/sales_order_calendar.js",
}

# Extra JS for tree views
doctype_tree_js = {
    "Account": "public/js/account_tree.js",
}

# App-wide JS bundle (loaded on all pages)
app_include_js = [
    "assets/my_app/js/my_app.min.js",
]
app_include_css = [
    "assets/my_app/css/my_app.min.css",
]

# Portal-only assets
web_include_js = ["assets/my_app/js/portal.min.js"]
web_include_css = ["assets/my_app/css/portal.min.css"]
```

## Fixtures (Data Migration)
```python
# Documents exported with bench export-fixtures
# and imported during app install/migrate
fixtures = [
    "Custom Field",                    # Export all Custom Fields
    "Property Setter",
    "Print Format",
    {
        "dt": "Custom Field",
        "filters": [["module", "=", "My App"]]  # Filtered export
    },
    {
        "dt": "Client Script",
        "filters": [["module", "=", "My App"]]
    }
]
```

## Website / Portal
```python
# Add routes for portal pages
website_route_rules = [
    {"from_route": "/orders", "to_route": "orders"},
    {"from_route": "/orders/<name>", "to_route": "order-detail"},
]

# Portal menu items
portal_menu_items = [
    {"title": "My Orders", "route": "/orders", "reference_doctype": "Sales Order"},
]

# Jinja environment customization
jinja = {
    "methods": "my_app.utils.jinja_methods",
    "filters": "my_app.utils.jinja_filters",
}

# Standard generators (pages created from DocType)
website_generators = ["Blog Post", "Web Page"]
```

## Permissions & Security
```python
# Add permission query conditions (row-level security)
permission_query_conditions = {
    "Sales Order": "my_app.permissions.get_permission_query_conditions",
}

# has_permission override
has_permission = {
    "Sales Order": "my_app.permissions.has_permission",
}
```

## Installation & Migration
```python
# Functions called during app install
before_install = "my_app.setup.before_install"
after_install = "my_app.setup.after_install"
after_app_install = "my_app.setup.after_app_install"

# Functions called during app uninstall
before_uninstall = "my_app.setup.before_uninstall"
after_uninstall = "my_app.setup.after_uninstall"

# Functions called during bench migrate
before_migrate = "my_app.setup.before_migrate"
after_migrate = "my_app.setup.after_migrate"

# Functions called at site creation
after_sync = "my_app.setup.after_sync"
```

## Notifications & Workflows
```python
# Notification templates
notification_config = "my_app.notifications.get_notification_config"

# Workflow state field
workflow_state_field = "workflow_state"

# Auto-assignment
auto_cancel_exempted_doctypes = ["Payment Entry"]
```

## Standard Page Overrides
```python
# Replace standard pages
standard_portal_menu_items = [...]

# Extend bootinfo (sent to browser on login)
extend_bootinfo = "my_app.boot.extend_bootinfo"

# Sounds
sounds = [
    {"name": "my-sound", "src": "/assets/my_app/audio/my_sound.mp3"}
]
```

## ERPNext-Specific Hooks
```python
# Regional: add country-specific payroll components
regional_overrides = {
    "India": {
        "erpnext.payroll.doctype.salary_slip.salary_slip.SalarySlip": 
            "my_app.regional.india.CustomSalarySlip"
    }
}

# Accounting dimensions
get_default_cost_center = "my_app.utils.get_default_cost_center"
```
