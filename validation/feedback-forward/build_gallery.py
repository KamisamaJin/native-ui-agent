#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Link original state-bound images; no synthetic reference or regenerated UI."""
import argparse,os
import study as s
R=s.R

def build():
 s.gate.authorize(R/'gates','reveal',R);assignment=s.read(R/'private/assignment.json')
 lines=['# 原始界面与逐状态采集','','全部图片为原采集字节；本页不重画、修图或重新渲染。完整来源、覆盖与输入/事件绑定见同目录 observation.json。长内容须检查整个状态的图集，首末图片链接不是完整覆盖的替代。','']
 roots=[]
 for task in ['T1','T2']:
  roots.append((task,'相同初始 PR',R/'corpora'/task/'d0',['P1','P2']))
  for alias,unit in assignment['gradeAliases'][task].items():
   roots.append((task,assignment['units'][unit]['tool']+' / '+unit,R/'corpora'/unit/'final-public',['P1','P2']))
 for task,label,root,cases in roots:
  for pl in ['ios','android']:
   for name in cases:
    raw=root/pl/name/'native';op=raw/'observation.json';lines+=['## '+task+' / '+label+' / '+pl+' / '+name,'']
    if not op.is_file():lines+=['原始采集未产生 observation，失败记录保留。',''];continue
    obs=s.read(op);link=lambda path:os.path.relpath(path,R)
    lines+=['[原始观测]('+link(op)+')','','| 状态 | 原始快照索引 | 首帧 | 末帧 | 完整覆盖 |','| --- | --- | --- | --- | --- |']
    snapshots={i:v for i,v in enumerate(obs.get('snapshots',[]))};first=None
    for cap in obs.get('state_captures',[]):
     indices=cap.get('snapshot_indices',[]);pictures=[(i,raw/snapshots[i]['screenshot'])for i in indices if i in snapshots and snapshots[i].get('screenshot')]
     refs=['[图 '+str(i)+']('+link(p)+')'for i,p in pictures]
     lines.append('| '+str(cap['state_id'])+' | '+', '.join(map(str,indices))+' | '+(refs[0]if refs else'缺失')+' | '+(refs[-1]if refs else'缺失')+' | '+str(cap.get('complete'))+' |')
     if first is None and pictures:first=pictures[0][1]
    lines.append('')
    if name=='P2'and first:lines+=['![窄屏原始首帧]('+link(first)+')','']
 return '\n'.join(lines)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();value=build();path=R/'GALLERY.md'
 if a.check:assert path.read_text()==value
 else:
  with path.open('x')as stream:stream.write(value)
 print('PASS original gallery links')
