# JavaScript API Reference

## Form API (frappe.ui.form)

### frm Object Methods
```javascript
// Field access
frm.get_field('fieldname')           // Get field control object
frm.get_value('fieldname')           // Get field value
frm.set_value('fieldname', value)    // Set field value (triggers change events)
frm.set_value({f1: v1, f2: v2})     // Set multiple fields

// Display
frm.refresh_field('fieldname')       // Re-render a field
frm.refresh_fields(['f1', 'f2'])
frm.refresh()                        // Full form refresh

// Visibility & State
frm.toggle_display('fieldname', show_bool)
frm.toggle_display(['f1', 'f2'], show_bool)
frm.toggle_reqd('fieldname', reqd_bool)    // Make required/optional
frm.toggle_enable('fieldname', enable_bool) // Enable/disable
frm.set_df_property('fieldname', 'property', value)
// Common properties: hidden, read_only, reqd, options, bold, description

// Queries on Link fields
frm.set_query('fieldname', function() {
    return {
        filters: { is_active: 1 },
        query: 'my_app.queries.get_filtered_items'  // server-side query
    };
});
frm.set_query('fieldname', 'child_table', function(doc, cdt, cdn) {
    let row = locals[cdt][cdn];
    return { filters: { 'item_group': row.item_group } };
});

// Buttons
frm.add_custom_button('Button Label', function() {
    // action
});
frm.add_custom_button('Button Label', function() {}, 'Group Name');
frm.clear_custom_buttons();
frm.change_custom_button_type('Button Label', 'Group', 'primary'); // type: primary/danger/default

// Indicators
frm.set_indicator_formatter('fieldname', function(doc) {
    return doc.status === 'Active' ? 'green' : 'red';
});

// Intro / Alert
frm.set_intro('Message to show at top of form', 'blue'); // blue/green/orange/red
frm.dashboard.set_headline('Message');

// Attachments
frm.attachments.get_attachments();

// Save & Submit
frm.save();
frm.save('Submit');   // 'Save'|'Submit'|'Update'|'Cancel'|'Amend'
frm.savesubmit();
frm.savecancel();

// Server call on document
frm.call('controller_method', {arg: value}).then(r => {
    console.log(r.message);
});
```

### Form Event Hooks
```javascript
frappe.ui.form.on('DocType Name', {
    // Lifecycle
    setup: (frm) => {},              // Once per form class creation
    onload: (frm) => {},             // When form data loaded
    onload_post_render: (frm) => {}, // After form rendered
    refresh: (frm) => {},            // Every refresh/navigation
    validate: (frm) => {},           // Before save client-side
    before_save: (frm) => {},
    after_save: (frm) => {},
    before_submit: (frm) => {},
    after_submit: (frm) => {},
    before_cancel: (frm) => {},
    after_cancel: (frm) => {},
    
    // Field change — named after fieldname
    customer: (frm) => {},
    qty: (frm) => {},
    
    // Timeline
    timeline_refresh: (frm) => {},
});

// Child table events
frappe.ui.form.on('Child DocType', {
    // Row events
    items_add: (frm, cdt, cdn) => {},      // Row added
    items_remove: (frm, cdt, cdn) => {},   // Row removed
    before_items_remove: (frm, cdt, cdn) => {},
    
    // Field events in child
    qty: (frm, cdt, cdn) => {
        let row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, 'amount', row.qty * row.rate);
    },
});
```

## Database API (client-side)

```javascript
// frappe.db — all return Promises
frappe.db.get_doc('Sales Order', 'SAL-ORD-00001')
    .then(doc => console.log(doc));

frappe.db.get_value('Customer', 'ACME-001', 'customer_name')
    .then(r => console.log(r.message.customer_name));

frappe.db.get_value('Customer', 'ACME-001', ['customer_name', 'email_id'])
    .then(r => console.log(r.message));

frappe.db.get_list('Sales Order', {
    filters: [['status', '=', 'Open']],
    fields: ['name', 'customer', 'grand_total'],
    order_by: 'transaction_date desc',
    limit: 20
}).then(list => console.log(list));

frappe.db.get_single_value('System Settings', 'language')
    .then(value => console.log(value));

frappe.db.insert({ doctype: 'Note', title: 'Test' })
    .then(doc => console.log(doc.name));

frappe.db.set_value('Sales Order', 'SAL-ORD-00001', 'status', 'Closed')
    .then(r => frm.reload_doc());

frappe.db.delete_doc('Note', 'NOTE-001');

frappe.db.exists('Customer', 'ACME-001')
    .then(exists => console.log(exists)); // returns name or undefined

frappe.db.count('Sales Order', { filters: { status: 'Open' } })
    .then(count => console.log(count));
```

## Server Calls

```javascript
// Standard call
frappe.call({
    method: 'my_app.api.my_function',
    args: { param1: 'value1' },
    callback: r => console.log(r.message),
    freeze: true,
    freeze_message: 'Processing...',
    error: (r) => console.error(r),
    always: () => {},   // runs regardless of success/failure
});

// Promise style
frappe.call('my_app.api.my_function', { param1: 'value1' })
    .then(r => console.log(r.message));
```

## Dialog API

```javascript
// Confirm dialog
frappe.confirm('Are you sure?', 
    () => { /* yes */ }, 
    () => { /* no */ }
);

// Prompt (single field)
frappe.prompt('Enter reason', (values) => {
    console.log(values.value);
}, 'Reason', 'Submit');

// Full dialog
let d = new frappe.ui.Dialog({
    title: 'My Dialog',
    fields: [
        { label: 'Name', fieldname: 'name', fieldtype: 'Data', reqd: 1 },
        { label: 'Date', fieldname: 'date', fieldtype: 'Date' },
        { fieldtype: 'Column Break' },
        { label: 'Amount', fieldname: 'amount', fieldtype: 'Currency' },
    ],
    primary_action_label: 'Submit',
    primary_action(values) {
        console.log(values);
        d.hide();
    }
});
d.show();
d.get_value('name');
d.set_value('name', 'John');
```

## Toasts & Messages

```javascript
frappe.show_alert({ message: 'Saved!', indicator: 'green' }, 5); // 5s
frappe.msgprint('A message');
frappe.msgprint({ title: 'Error', message: 'Something went wrong', indicator: 'red' });
frappe.throw('Cannot proceed'); // shows error dialog
```

## Routing

```javascript
frappe.set_route('Form', 'Sales Order', 'SAL-ORD-00001');
frappe.set_route('List', 'Sales Order');
frappe.set_route('List', 'Sales Order', 'Kanban', 'Board Name');
frappe.set_route('query-report', 'Sales Analytics');
frappe.set_route('page', 'my-page');
frappe.get_route();   // returns current route array
frappe.get_prev_route();
```

## Model Utilities

```javascript
frappe.model.get_value(cdt, cdn, fieldname)
frappe.model.set_value(cdt, cdn, fieldname, value)
frappe.model.get_doc(doctype, name)   // from locals (client cache)
frappe.model.add_child(doc, child_doctype, parentfield)
frappe.model.clear_table(doc, fieldname)  // Clear child table

// Field meta
frappe.meta.get_docfield(doctype, fieldname)
frappe.meta.get_label(doctype, fieldname)
frappe.meta.is_single(doctype)
```

## Realtime (Socket.io)

```javascript
// Subscribe to events
frappe.realtime.on('my_event', (data) => {
    console.log(data);
});

// Unsubscribe
frappe.realtime.off('my_event');

// In Python — publish:
frappe.publish_realtime('my_event', {'key': 'value'}, user='user@example.com')
frappe.publish_realtime('my_event', data, room=frappe.local.site) // all users
```

## Common Utilities

```javascript
frappe.datetime.now_datetime()    // '2024-01-15 10:30:00'
frappe.datetime.now_date()        // '2024-01-15'
frappe.datetime.add_days(date, n)
frappe.datetime.str_to_obj(str)   // Parse date string

frappe.format(value, df, options, doc)  // Format value for display
frappe.format_currency(value, currency, precision)

frappe.get_route_str()
frappe.get_url()
frappe.utils.play_sound('submit')  // 'submit'|'cancel'|'error'

// User & Session
frappe.session.user
frappe.session.user_fullname
frappe.boot.user.roles              // Current user's roles
frappe.user.has_role('Manager')
frappe.user.is_report_manager()
```
