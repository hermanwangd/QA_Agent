import unittest

from dummy_app.app import OrderStore


class OrderStoreTests(unittest.TestCase):
    def test_health_reports_ready_status(self):
        store = OrderStore()

        self.assertEqual(store.health(), {"status": "UP", "service": "dummy-order-app"})

    def test_create_order_returns_deterministic_accepted_order(self):
        store = OrderStore()

        result = store.create_order(
            {
                "customer_id": "CUST-001",
                "sku": "SKU-PI-RUN",
                "quantity": 2,
            }
        )

        self.assertEqual(
            result,
            {
                "id": "ORD-0001",
                "customer_id": "CUST-001",
                "sku": "SKU-PI-RUN",
                "quantity": 2,
                "status": "ACCEPTED",
            },
        )

    def test_get_order_returns_existing_order(self):
        store = OrderStore()
        created = store.create_order(
            {
                "customer_id": "CUST-002",
                "sku": "SKU-LOOKUP",
                "quantity": 1,
            }
        )

        self.assertEqual(store.get_order("ORD-0001"), created)

    def test_get_missing_order_returns_none(self):
        store = OrderStore()

        self.assertIsNone(store.get_order("ORD-404"))


if __name__ == "__main__":
    unittest.main()
