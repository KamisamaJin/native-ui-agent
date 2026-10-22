import hashlib
from pathlib import Path
import tempfile
import unittest
import publication_closure as closure

H = hashlib.sha256(b'original').hexdigest()


class PublicationClosureTests(unittest.TestCase):
    def test_exact_dependency(self):
        self.assertEqual(closure.audit({'a/file': H}, {'a/file': H})['directCount'], 1)

    def test_unpublished_dependency_is_not_hidden_by_local_file(self):
        with self.assertRaisesRegex(ValueError, 'Missing'):
            closure.audit({'a/result/blob': H}, {})

    def test_different_bytes_cannot_satisfy_exact_path(self):
        with self.assertRaises(ValueError):
            closure.audit({'a/file': H}, {'a/file': '0' * 64})

    def test_unique_case_only_alias(self):
        result = closure.audit({'design/Seal.JSON': H}, {'design/seal.json': H})
        self.assertEqual(result['caseAliases'], [{'requested': 'design/Seal.JSON', 'published': 'design/seal.json', 'sha256': H}])

    def test_case_ambiguity_and_wrong_bytes_rejected(self):
        for files in [{'a/FILE': H, 'a/file': H}, {'a/file': '0' * 64}]:
            with self.assertRaises(ValueError):
                closure.audit({'a/File': H}, files)

    def test_paths_cannot_escape_or_change_normalization(self):
        for path in ['../file', '/file', 'a/../file', './file']:
            with self.assertRaises(ValueError):
                closure.audit({path: H}, {})

    def test_materialization_requires_original_bytes_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root / 'source').write_bytes(b'original')
            alias = {'requested': 'nested/target', 'published': 'source', 'sha256': H}
            closure.prepare(root, [alias]); self.assertEqual((root / 'nested/target').read_bytes(), b'original')
            (root / 'nested/target').write_bytes(b'changed')
            with self.assertRaises(ValueError):
                closure.prepare(root, [alias])


if __name__ == '__main__':
    unittest.main()
