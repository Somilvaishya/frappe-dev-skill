# Testing Reference

## Unit Tests

### Test File Structure
```python
# my_app/my_module/doctype/sales_order/test_sales_order.py
import frappe
import unittest
from frappe.tests.utils import FrappeTestCase

class TestSalesOrder(FrappeTestCase):
    """Tests for SalesOrder DocType"""
    
    def setUp(self):
        """Run before each test"""
        # Create test fixtures
        self.customer = self._make_customer()
    
    def tearDown(self):
        """Run after each test — cleanup"""
        frappe.db.rollback()  # Or selectively delete
    
    def test_validation_requires_items(self):
        """Test that orders without items raise validation error"""
        so = frappe.new_doc('Sales Order')
        so.customer = self.customer
        so.transaction_date = frappe.utils.today()
        
        with self.assertRaises(frappe.ValidationError):
            so.insert()
    
    def test_totals_calculated_correctly(self):
        """Test total calculation logic"""
        so = self._make_sales_order()
        self.assertEqual(so.total, 500.0)
        self.assertEqual(so.grand_total, so.total + so.tax_amount)
    
    def test_on_submit_creates_delivery(self):
        """Test that submitting creates a Delivery Note"""
        so = self._make_sales_order()
        so.submit()
        
        delivery_notes = frappe.get_all(
            'Delivery Note', 
            filters={'sales_order': so.name}
        )
        self.assertTrue(len(delivery_notes) > 0)
    
    def _make_customer(self):
        """Helper: create test customer"""
        customer = frappe.get_doc({
            'doctype': 'Customer',
            'customer_name': f'_Test Customer {frappe.utils.random_string(5)}',
            'customer_type': 'Company',
            'customer_group': 'All Customer Groups',
            'territory': 'All Territories'
        }).insert(ignore_permissions=True)
        return customer.name
    
    def _make_sales_order(self):
        """Helper: create valid test sales order"""
        so = frappe.get_doc({
            'doctype': 'Sales Order',
            'customer': self.customer,
            'transaction_date': frappe.utils.today(),
            'delivery_date': frappe.utils.add_days(frappe.utils.today(), 7),
            'items': [{
                'item_code': '_Test Item',
                'qty': 10,
                'rate': 50,
                'delivery_date': frappe.utils.add_days(frappe.utils.today(), 7),
            }]
        }).insert(ignore_permissions=True)
        return so
```

### Running Tests
```bash
# Run all tests for an app
bench --site testsite.localhost run-tests --app my_app

# Run tests for a specific DocType
bench --site testsite.localhost run-tests --doctype "Sales Order"

# Run a specific test module
bench --site testsite.localhost run-tests \
  --module my_app.my_module.doctype.sales_order.test_sales_order

# Run a specific test method
bench --site testsite.localhost run-tests \
  --module my_app.my_module.doctype.sales_order.test_sales_order \
  --test test_validation_requires_items

# Run with coverage
bench --site testsite.localhost run-tests --app my_app --coverage
```

---

## Test Fixtures & Test Records

```python
# frappe provides _Test records for standard doctypes
# They are created by frappe.test_runner automatically

# Access standard test records:
frappe.get_doc('Customer', '_Test Customer')
frappe.get_doc('Item', '_Test Item')
frappe.get_doc('Company', '_Test Company')

# Custom test records: my_app/fixtures/test_records.json
# OR in test file:
test_records = [
    {
        'doctype': 'My DocType',
        'field1': 'value1',
        'field2': 'value2',
    }
]
```

---

## FrappeTestCase Utilities

```python
from frappe.tests.utils import FrappeTestCase

class MyTest(FrappeTestCase):
    # Assertions
    self.assertDocumentEqual(expected_dict, actual_doc)
    self.assertFalse(condition)
    self.assertTrue(condition)
    self.assertEqual(expected, actual)
    
    # Context managers
    with self.assertRaises(frappe.ValidationError):
        risky_operation()
    
    with self.assertQueryCount(5):
        # Ensures no more than 5 DB queries are made
        my_function()
    
    # Disable/enable features for testing
    with self.toggle_feature('some_flag', True):
        test_with_flag()
    
    # Mock background jobs (don't actually enqueue)
    with self.captureOnCommitHooks():
        doc.save()
```

---

## API Testing (frappe.tests)

```python
# Test REST API endpoints
from frappe.tests.utils import FrappeTestCase

class TestAPI(FrappeTestCase):
    def test_get_item_price_api(self):
        from my_app.api import get_item_price
        
        # Direct function test
        price = get_item_price('_Test Item', 'Standard Selling')
        self.assertIsInstance(price, (int, float))
    
    def test_api_requires_auth(self):
        """Test that endpoint rejects unauthenticated access"""
        # frappe.local.session.user is set by test runner
        frappe.local.session.user = 'Guest'
        with self.assertRaises(frappe.PermissionError):
            get_item_price('_Test Item', 'Standard Selling')
```

---

## UI Testing (Cypress)

```javascript
// my_app/tests/ui/test_sales_order.spec.js
describe('Sales Order', () => {
    before(() => {
        cy.login();
        cy.visit('/app');
    });
    
    it('creates a new sales order', () => {
        cy.visit('/app/sales-order/new-sales-order-1');
        cy.get('[data-fieldname="customer"]').type('_Test Customer');
        cy.get('.frappe-list .list-item').first().click();
        
        cy.get('[data-fieldname="transaction_date"]')
            .should('have.value', frappe.datetime.nowdate());
        
        // Add item
        cy.get('.grid-add-row').click();
        cy.get('[data-fieldname="item_code"] input').type('_Test Item');
        cy.get('.frappe-list .list-item').first().click();
        
        cy.get('[data-fieldname="qty"] input').clear().type('5');
        
        // Save
        cy.get('.btn-primary').contains('Save').click();
        cy.get('.msgprint').should('not.exist');
        cy.get('.indicator.blue').should('contain', 'Saved');
    });
    
    it('validates required fields', () => {
        cy.visit('/app/sales-order/new-sales-order-1');
        cy.get('.btn-primary').contains('Save').click();
        cy.get('.msgprint').should('contain', 'customer');
    });
});
```

```bash
# Run UI tests
bench run-ui-tests my_app
# or
cd frappe-bench && npx cypress run --spec "apps/my_app/my_app/tests/**"
```

---

## Test Best Practices

1. **Always rollback** in tearDown — don't rely on database state between tests.
2. **Use unique names** for test records — `frappe.utils.random_string(5)` suffix.
3. **Mock external calls** — use `unittest.mock.patch` for email, HTTP requests.
4. **Test the boundary conditions** — empty, null, max values, special characters.
5. **Test permissions explicitly** — switch users: `frappe.set_user('test@example.com')`.
6. **Prefer unit tests** over integration tests for speed.
7. **Name tests descriptively** — `test_validation_fails_when_items_empty`.

```python
# Switching users in tests
class TestPermissions(FrappeTestCase):
    def test_non_manager_cannot_approve(self):
        frappe.set_user('test_regular_user@example.com')
        try:
            doc = frappe.get_doc('Sales Order', self.order_name)
            with self.assertRaises(frappe.PermissionError):
                doc.approve_order()
        finally:
            frappe.set_user('Administrator')  # Always restore!
```
