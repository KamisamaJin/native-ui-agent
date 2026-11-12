import unittest
from cleanup_identity_v1 import unchanged


class MetadataIdentity(unittest.TestCase):
    def setUp(self):
        self.before = [1, 2, 0o100444, 501, 20, 3, 100, 1000, 1001, 4096]

    def test_allocator_observation_is_not_content_identity(self):
        after = self.before[:]
        after[9] = 8192
        self.assertTrue(unchanged(self.before, after, 0))

    def test_exact_own_link_ledger(self):
        after = self.before[:]
        after[5] -= 1
        after[8] += 100
        self.assertTrue(unchanged(self.before, after, 1))

    def test_each_namespace_content_field_blocks(self):
        for index in [0, 1, 2, 3, 4, 5, 6, 7, 8]:
            with self.subTest(index=index):
                after = self.before[:]
                after[index] += 1
                self.assertFalse(unchanged(self.before, after, 0))

    def test_unexplained_alias_count_blocks(self):
        after = self.before[:]
        after[5] -= 2
        self.assertFalse(unchanged(self.before, after, 1))


if __name__ == '__main__':
    unittest.main()
