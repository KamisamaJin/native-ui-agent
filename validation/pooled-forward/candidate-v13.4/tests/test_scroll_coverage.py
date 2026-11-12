"""SIMULATED raster/AX strips, independent of any application requirement."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import scroll_coverage as coverage


class ScrollCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.binding = {'pid': 42, 'instance': 'native-test-session', 'fixture_index': 0,
                        'input_sha256': 'a' * 64, 'event_revision': 0}
        self.canvas = Image.new('RGB', (32, 430), 'white'); draw = ImageDraw.Draw(self.canvas)
        for row in range(42): draw.rectangle((2, row * 10 + 1, 22, row * 10 + 8), fill=((row * 17) % 256, 60, (row * 31) % 256))
        self.found = []
        for index, (offset, height) in enumerate([(0, 500), (90, 490), (180, 460), (270, 440), (310, 430)]):
            file = str(index) + '.png'; self.canvas.crop((0, offset, 32, offset + 120)).save(self.root / file)
            nodes = [{'index': 0, 'parent_index': -1, 'identifier': '__observer.scroll'}]
            for row in range(42):
                y = row * 10 + 1 - offset
                nodes.append({'index': row + 1, 'parent_index': 0, 'identifier': '', 'label': 'Unique landmark ' + str(row), 'role_raw': 48,
                              'value': None, 'enabled': True, 'selected': False,
                              'frame': {'x': 2, 'y': y, 'width': 21, 'height': 8}, 'fully_within_viewport': 0 <= y and y + 8 <= 120})
            if index == 4: nodes.append({'index': 99, 'parent_index': 0, 'identifier': '__observer.bottom', 'fully_within_viewport': True})
            self.found.append((index, {'binding': self.binding, 'binding_after_capture': self.binding, 'capture_consistent': True,
                  'viewport': {'x': 0, 'y': 0, 'width': 32, 'height': 120}, 'app_frame': {'x': 0, 'y': 0, 'width': 32, 'height': 120},
                  'runtime': {'content_frame': {'x': 0, 'y': -offset, 'width': 32, 'height': height}},
                  'screenshot_pixels': {'width': 32, 'height': 120}, 'screenshot': file, 'nodes': nodes,
                  'bottom_sentinel_visible': index == 4}))

    def certify(self, found=None): return coverage.certify(found or self.found, self.binding, self.root)

    def test_lazy_estimate_drift_requires_exact_connected_original_pixels_and_leaves(self):
        result = self.certify(); self.assertTrue(result['complete'], result)
        self.assertEqual(len(result['links']), 4); self.assertEqual(result['observed_terminal_height'], 430)
        self.assertEqual(result['estimated_heights'], [500, 490, 460, 440, 430])

    def test_pixel_change_is_unknown_even_with_unchanged_native_leaves(self):
        path = self.root / '1.png'
        with Image.open(path) as original: im = original.convert('RGB')
        im.putpixel((30, 5), (1, 2, 3)); im.save(path)
        self.assertFalse(self.certify()['complete'])

    def test_sparse_or_duplicate_or_container_landmarks_cannot_be_guessed(self):
        for mode in ['sparse', 'duplicate', 'container']:
            found = copy.deepcopy(self.found)
            for _, s in found:
                for n in s['nodes'][1:]:
                    if n.get('identifier') == '__observer.bottom': continue
                    if mode == 'sparse': n['fully_within_viewport'] = False
                    elif mode == 'duplicate': n['label'] = 'repeated'
                    else: s['nodes'].append({'index': 1000 + n['index'], 'parent_index': n['index'], 'identifier': ''})
            self.assertFalse(self.certify(found)['complete'], mode)

    def test_reflow_content_traits_epoch_grid_and_gap_reject(self):
        for mode in ['geometry', 'label', 'value', 'epoch', 'grid', 'gap', 'terminal']:
            found = copy.deepcopy(self.found); s = found[1][1]
            if mode == 'geometry': s['nodes'][12]['frame']['y'] += 1
            elif mode == 'label': s['nodes'][12]['identifier'] = 'fixed'; found[0][1]['nodes'][12]['identifier'] = 'fixed'; s['nodes'][12]['label'] = 'changed'
            elif mode == 'value': s['nodes'][12]['value'] = 'changed'
            elif mode == 'epoch': s['binding'] = dict(s['binding'], event_revision=1)
            elif mode == 'grid': s['runtime']['content_frame']['y'] -= .25
            elif mode == 'gap': found.pop(1)
            else: found[-1][1]['bottom_sentinel_visible'] = False
            self.assertFalse(self.certify(found)['complete'], mode)

    def test_missing_images_root_or_epoch_never_earns_coverage(self):
        self.assertFalse(coverage.certify(self.found, self.binding, None)['complete'])
        self.assertFalse(coverage.certify(self.found, {}, self.root)['complete'])
        (self.root / '2.png').unlink(); self.assertFalse(self.certify()['complete'])


if __name__ == '__main__': unittest.main()
