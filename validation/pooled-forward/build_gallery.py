#!/usr/bin/env python3
"""Byte-exact deterministic previews, never a visual verdict or design oracle.

For every anonymous I/X/Y version and platform, choose snapshot index0 of its
original private capture. Missing data stays visibly missing. No cropping,
retouching, defect-based selection, assignment access or native execution.
"""
import argparse
import hashlib
import html
import json
from pathlib import Path, PurePosixPath

GROUPS = {'Case0%d-%s' % (i, version) for i in range(1, 6) for version in ['I', 'X', 'Y']}


def need(ok, why):
    if not ok: raise ValueError(why)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def relative(raw):
    path = PurePosixPath(raw)
    need(type(raw) is str and raw and '\\' not in raw and not path.is_absolute()
         and str(path) == raw and '..' not in path.parts, 'Original safe packet member required')
    return path


def original(reference):
    path = Path(reference['path'])
    need(path.is_absolute(), 'Original absolute packet authority required')
    for part in [path, *path.parents]: need(not part.is_symlink(), 'No packet symlinks')
    raw = path.read_bytes(); need(sha(raw) == reference['sha256'], 'Original pinned preview input differs')
    return json.loads(raw)


def build(index_ref, output):
    index = original(index_ref)
    need(index['kind'] == 'global-independent-cause-grade-barrier' and len(index['groups']) == 15
         and {r['group'] for r in index['groups']} == GROUPS, 'Complete original fifteen-version cause index required')
    need(not output.exists(), 'Fresh gallery directory required'); output.mkdir(parents=True)
    images = output/'images'; images.mkdir(); records = []
    for row in sorted(index['groups'], key=lambda item: item['group']):
        group = row['group']; packets = []
        for ref in row['inputs']:
            value = original(ref)
            if value.get('kind') == 'anonymous-fixed-version-input-seal': packets.append((ref, value))
        need(len(packets) == 1, 'Exactly one original own-version packet required')
        packet_ref, seal = packets[0]; root = Path(packet_ref['path']).parent
        need(seal['anonymous_group'] == group, 'Preview packet group differs')
        def member(name):
            name = str(relative(name)); path = root/name
            for part in [path, *path.parents]: need(not part.is_symlink(), 'No image/observation symlinks')
            raw = path.read_bytes(); need(sha(raw) == seal['files'][name], 'Selected original preview bytes differ')
            return raw
        packet = json.loads(member('PACKET.json')); need(packet['anonymous_group'] == group, 'Packet description differs')
        for platform in ['ios', 'android']:
            candidates = [x for x in packet['observations'] if x['family'] == 'private' and x['platform'] == platform]
            need(len(candidates) == 1, 'Exactly one original private platform observation required')
            entry = candidates[0]; record = {'group': group, 'platform': platform, 'packet_seal': packet_ref,
                'observation_id': entry['id'], 'selection': 'Original private snapshot index0, without looking for defects'}
            if not entry.get('facts_available'):
                record.update(available=False, reason='Original private native facts unavailable')
            else:
                obs_ref = entry['native_observation']; observation = json.loads(member(obs_ref)); snapshots = observation.get('snapshots', [])
                if not snapshots: record.update(available=False, reason='No original snapshot0; no replacement chosen')
                else:
                    snapshot = snapshots[0]; image_ref = str(PurePosixPath(obs_ref).parent/relative(snapshot['screenshot']))
                    raw = member(image_ref); need(raw.startswith(b'\x89PNG\r\n\x1a\n'), 'Original native PNG expected')
                    filename = group+'-'+platform+'.png'; destination = images/filename
                    with destination.open('xb') as stream: stream.write(raw)
                    destination.chmod(0o444)
                    record.update(available=True, file='images/'+filename, sha256=sha(raw), bytes=len(raw),
                        original_packet_image=image_ref, original_packet_observation=obs_ref,
                        original_observation_sha256=entry['original_observation_sha256'], snapshot_index=0,
                        state_id=snapshot.get('state_id'), binding=snapshot.get('binding'))
            records.append(record)
    by = {(x['group'], x['platform']): x for x in records}
    title = 'Five anonymous native tasks: fixed first-frame previews'
    text = ['<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>'+title+'</title><style>body{font:16px system-ui;margin:24px;background:#f4f4f4;color:#17202a}table{table-layout:fixed;width:100%;border-collapse:collapse}td,th{border:1px solid #bbb;padding:12px;vertical-align:top}img{display:block;width:100%;max-width:402px;height:auto;margin:auto}small{overflow-wrap:anywhere}h2{margin-top:40px}</style>',
        '<h1>'+title+'</h1><p>每个版本固定展示原始私有采集的第0帧。I为公共初版，X/Y为匿名最终版本；本页不选择缺陷帧、不裁切、不修图，也不构成设计参考或质量结论。完整状态、原图和失败记录另有封存。PNG与原始包逐字节相同。</p>']
    for case in ['Case%02d' % i for i in range(1, 6)]:
        for platform in ['ios', 'android']:
            text.append('<h2>'+case+' / '+platform+'</h2><table><tr><th>I</th><th>X</th><th>Y</th></tr><tr>')
            for version in ['I', 'X', 'Y']:
                row = by[(case+'-'+version, platform)]
                if row['available']:
                    escaped = html.escape(row['file'], quote=True)
                    text.append('<td><a href="'+escaped+'"><img src="'+escaped+'" alt="'+row['group']+' '+platform+' original frame0"></a><small>state '+html.escape(str(row['state_id']))+'<br>SHA256 '+row['sha256']+'</small></td>')
                else: text.append('<td>'+html.escape(row['reason'])+'</td>')
            text.append('</tr></table>')
    text.append('</html>')
    (output/'index.html').write_text('\n'.join(text)+'\n'); (output/'index.html').chmod(0o444)
    manifest = {'version': 1, 'kind': 'deterministic-byte-exact-native-preview-gallery', 'input': index_ref,
        'records': records, 'quality_verdicts': False, 'assignment_read': False, 'image_editing': False,
        'scope': 'Exactly private snapshot0 per original group/platform or explicit missing; no first-success fallback. Preview only, not complete state coverage, normative design, current-source eligibility or product grading.'}
    (output/'MANIFEST.json').write_text(json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False)+'\n')
    (output/'MANIFEST.json').chmod(0o444)
    return {'slots': len(records), 'available': sum(x['available'] for x in records),
        'manifest_sha256': sha((output/'MANIFEST.json').read_bytes()), 'native_execution': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cause-index', type=Path, required=True); parser.add_argument('--cause-index-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True); args = parser.parse_args()
    print(json.dumps(build({'path': str(args.cause_index), 'sha256': args.cause_index_sha256}, args.output.resolve())))


if __name__ == '__main__': main()
