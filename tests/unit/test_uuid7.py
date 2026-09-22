import time
import unittest
import uuid

from visual_harness.events._uuid7 import uuid7


class TestUUID7(unittest.TestCase):
    def test_returns_uuid_instance(self):
        self.assertIsInstance(uuid7(), uuid.UUID)

    def test_version_is_7(self):
        self.assertEqual(uuid7().version, 7)

    def test_variant_is_rfc4122(self):
        self.assertEqual(uuid7().variant, uuid.RFC_4122)

    def test_successive_ids_are_time_sortable(self):
        first = uuid7()
        time.sleep(0.005)
        second = uuid7()
        self.assertLess(first.int >> 80, second.int >> 80)


if __name__ == "__main__":
    unittest.main()
