import importlib.util
import hashlib
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('historical_sources', Path(__file__).with_name('historical_sources.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class HistoricalSourceTests(unittest.TestCase):
    def test_changed_current_document_uses_exact_archive_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            live = root/'NOTICE.md'; live.write_bytes(b'current documentation')
            archive = root/'validation/version/historical-root/NOTICE.md'
            archive.parent.mkdir(parents=True); archive.write_bytes(b'original documentation')
            expected = hashlib.sha256(archive.read_bytes()).hexdigest()
            self.assertEqual(module.archived_source(root, 'NOTICE.md', expected), archive)
            self.assertEqual(live.read_bytes(), b'current documentation')
            self.assertEqual(archive.read_bytes(), b'original documentation')

    def test_matching_filename_with_wrong_bytes_never_satisfies_seal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            archive = root/'validation/version/historical-root/NOTICE.md'
            archive.parent.mkdir(parents=True); archive.write_bytes(b'different archive')
            with self.assertRaises(AssertionError):
                module.archived_source(root, 'NOTICE.md', hashlib.sha256(b'original').hexdigest())
            with self.assertRaises(ValueError):
                module.archived_source(root, '../NOTICE.md', '0'*64)

    def test_nested_adapter_alias_is_bound_to_original_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve(); relative = 'validation/publications/replay/verify.py'
            wrong = root/'validation/earlier/historical-root'/relative
            correct = root/'validation/later/historical-root'/relative
            for path, data in [(wrong, b'wrong'), (correct, b'original adapter')]:
                path.parent.mkdir(parents=True); path.write_bytes(data)
            self.assertEqual(module.archived_source(root, relative, hashlib.sha256(b'original adapter').hexdigest()), correct)


if __name__ == '__main__':
    unittest.main()
