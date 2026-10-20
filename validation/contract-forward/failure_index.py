#!/usr/bin/env python3
# coding: utf-8
"""List every unsuccessful native acquisition and explicit coverage gap."""
import argparse,json
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def build():
 commands=[];gaps=[];images=0
 for category in ['own-corpora','own-retries','common-corpora','paired-corpora']:
  for path in sorted((R/category).rglob('corpus.json')):
   data=read(path)
   if 'platformRuns'not in data:continue
   for platform,runs in data['platformRuns'].items():
    for row in runs:
     base=path.parent/platform/row['case'];r={'corpus':str(path.parent.relative_to(R)),'platform':platform,**row};commands.append(r)
     observation=base/'observation.json'
     r['nativeTestEntered']=observation.is_file()
     if not observation.is_file():
      r['failureReasons']=['Original frontend rejected offered width before native test.']
      continue
     summary=base/'native-summary.json'
     r['failureReasons']=[x['failureText']for x in read(summary).get('testFailures',[])]if summary.is_file()else[]
     obs=read(observation);images+=len(obs['snapshots'])
     for i,step in enumerate(obs.get('steps',[])):
      bundle=step.get('observation_set',{})
      if bundle and not bundle.get('all_targets_observed',False):gaps.append({'observation':str(observation.relative_to(R)),'stepIndex':i,'state':step.get('state'),'dispatch':step.get('dispatch'),'observation_set':bundle})
 return {'nativeCommandCount':len(commands),'nativeCommandWallSumSeconds':sum(x['wallSeconds']for x in commands),'snapshotRecords':images,'unsuccessfulNativeAcquisitions':[x for x in commands if x['exitCode']!=0],'incompletePostActionObservationSets':gaps,'scope':'Native failures and unknown targets are preserved. Nonzero test exit can coexist with usable state-bound observations; it is never converted into a whole-case pass. Common width recovery is separately attested in COMMON-WIDTH-AMENDMENT.json; its neutral probe is outside this trial command count.'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();data=build();path=R/'failure-index.json'
 text=['# 失败与未评估记录','',f"保留 {data['nativeCommandCount']} 条试验采集命令、{len(data['unsuccessfulNativeAcquisitions'])} 次非零退出、{data['snapshotRecords']} 个快照记录。命令数包含两次原生测试前的输入策略拒绝。",'', '| 语料 | 平台/场景 | 退出 | 命令秒数 | 实际原因 |','| --- | --- | ---: | ---: | --- |']
 for x in data['unsuccessfulNativeAcquisitions']:
  ref=x['corpus']+'/'+x['platform']+'/'+x['case']+'-command.json';text.append(f"| [{x['corpus']}]({ref}) | {x['platform']}/{x['case']} | {x['exitCode']} | {x['wallSeconds']:.3f} | {'; '.join(x['failureReasons'])} |")
 text+=['','原始两次 iOS P2 width300 拒绝没有观测或截图；共同 frontend 修复后在独立目录重试，原始语料保持不变。其他非零退出有实际原生观测，但 XCUITest 失败和缺目标仍保留，不能把有效数据等同于整例通过。','',f"未完整动作后观察集：{len(data['incompletePostActionObservationSets'])}；完整 target/dispatch/binding 见 [JSON](failure-index.json)。缺失目标和禁用刺激后的回调继续计 U。",'','首次独立 FINAL 报告曾将有源文件/构建绑定的观测误写为采集全部成功；[独立事实更正](evaluation/factual-addenda/FINAL-acquisition.json)保留原文、实际两次 exit1 和证据哈希，不重写已封存评分。','','工具 alpha 中 AX/layout 范围误用、独立通用探针的初始选择器拒绝/CLI 参数错误、设计批准前的脚本与控制错误也保留在 development/、independent-generic/ 和 design/private/preapproval-attempt-*；它们发生在业务源代码之前，不作为本轮产品修复成功案例。','']
 rendered='\n'.join(text);md=R/'FAILURES.md'
 if a.write:path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n');md.write_text(rendered)
 else:assert read(path)==data and md.read_text()==rendered
 print(json.dumps({'status':'PASS','commands':data['nativeCommandCount'],'nonzero':len(data['unsuccessfulNativeAcquisitions']),'snapshots':data['snapshotRecords'],'incompletePostActionSets':len(data['incompletePostActionObservationSets'])}))
if __name__=='__main__':main()
