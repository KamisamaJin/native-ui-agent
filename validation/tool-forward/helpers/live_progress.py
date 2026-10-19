#!/usr/bin/env python3
"""Read only XCTest progress metadata; no screenshot or UI outcome assessment."""
import argparse
import json
import re
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('capture', type=Path)
a = p.parse_args()
for path in a.capture.glob('test.xcresult/Staging/**/StandardOutputAndStandardError.txt'):
    text = path.read_text(errors='replace')
    times = re.findall(r't\s*=\s*([\d.]+)s', text)
    attachments = re.findall(r'attachment named ["\']([^"\']+)', text, re.I)
    print(json.dumps({'capture': str(a.capture),
                      'xctest_elapsed_seconds': float(times[-1]) if times else None,
                      'recorded_attachment_count': len(attachments),
                      'latest_attachment_names': attachments[-3:],
                      'find_operation_log_mentions': text.count('Find the'),
                      'scope': 'Read-only live diagnostic metadata. Not completed evidence, passing states or exact query CPU time.'}))
