#!/usr/bin/env python3
# coding: utf-8
"""Link original evidence images; do not replace or synthesize native pixels."""
import argparse,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');args=p.parse_args();assignment=read(R/'private/ASSIGNMENT-RELEASE.json');lines=['# 原始图片与修复范围','','参考线框表达结构与明确标注，不与原生字体进行跨渲染器像素回归。下面链接来自共同验收逐状态证据的原始 PNG；完整滚动和其他状态仍在各 observation.json。','','![独立 P2 参考](design/public/references/P2.png)','','| 组/平台，P2 browse 的 Reserve 可见帧 | 首版 | 修复后 |','| --- | --- | --- |'];inventory=[]
 for alias,unit in assignment['gradeAliases'].items():
  tool=assignment['units'][unit]['tool']
  for platform in ['ios','android']:
   cells=[]
   for stage in ['D0','FINAL']:
    g=read(R/'evaluation'/stage/alias/'final/P2'/platform/'grade.json');row=next(r for r in g['rows']if r['state']=='browse'and r['requirement']=='reserve-visible');obsref=row['evidence']['observation'];marker='/validation/contract-forward/';observation=R/obsref.split(marker,1)[1];obs=read(observation);idx=row['snapshot_indices'][0]if row['snapshot_indices']else None
    if idx is None:cells.append('未评估');continue
    image=observation.parent/obs['snapshots'][idx]['screenshot'];rel=str(image.relative_to(R));inventory.append({'tool':tool,'stage':stage,'case':'P2','platform':platform,'state':'browse','snapshot':idx,'path':rel,'sha256':sha(image)});cells.append(f'![{tool} {platform} {stage}]({rel})')
   lines.append('| '+tool+'/'+platform+' | '+' | '.join(cells)+' |')
 lines += ['','两组 iOS 修改了显式按钮样式以回应自身原始的禁用文本可读性疑虑；它属于未定量、未确认的质性问题，不能计为已验证 F→P。新版还把 Android Reserve 最小高度改为49dp；原始48dp设计下的数值边界 F 保留，不因此声称修复了用户可见产品缺陷。','', '截图不证明 iOS 计算字号、颜色、框架 padding 或物理点击区域。局部可见目标不代表全页内容已完整检查。',''];text='\n'.join(lines);out=R/'GALLERY.md';ledger=R/'gallery-images.json'
 if args.write:out.write_text(text);ledger.write_text(json.dumps(inventory,indent=2)+'\n')
 else:assert out.read_text()==text and read(ledger)==inventory
 print('PASS: gallery links SHA-bound original native frames')
if __name__=='__main__':main()
