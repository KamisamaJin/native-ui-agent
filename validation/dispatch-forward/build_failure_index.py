#!/usr/bin/env python3
"""Retain command/compile failures and every F/U score without relabeling them."""
import argparse,collections,json
from contract import R,read,sha
def compute():
 assert (R/'private/assignment-release.json').is_file()
 commands=[]
 for p in sorted((R/'evidence').rglob('*-command.json')):
  d=read(p)
  if not all(k in d for k in ['case','exitCode','wallSeconds']):continue
  commands.append({'artifact':str(p.relative_to(R)),'sha256':sha(p),'case':d['case'],'exitCode':d['exitCode'],'wallSeconds':d['wallSeconds'],'administrativeSuperseded':'administrative-first-d0'in p.parts,'publicIntegration':'public-integration'in p.parts})
 generic=[{'case':d['case'],'exitCode':d['native_exit_code'],'manifestSHA256':d['manifest_sha256']}for d in read(R/'generic-summary.json')['runs']if d['native_exit_code']!=0]
 compiles=[]
 def walk(value,pointer,path):
  if isinstance(value,dict):
   code=value.get('exit_code',value.get('exitCode'))
   if type(code)is int and code!=0:compiles.append({'artifact':str(path.relative_to(R)),'sha256':sha(path),'pointer':pointer,'record':value})
   for k,v in value.items():walk(v,pointer+'/'+k.replace('~','~0').replace('/','~1'),path)
  elif isinstance(value,list):
   for i,v in enumerate(value):walk(v,pointer+'/'+str(i),path)
 for p in sorted((R/'private/submissions').glob('*/repair.json')):walk(read(p),'',p)
 scores={}
 for phase in ['d0','final','paired-d0']:
  for folder in sorted((R/'design/private/evaluation'/phase).iterdir()):
   report=folder/('paired-grade.json'if phase=='paired-d0'else'grade.json');d=read(report);rows=d['rows'];scores[phase+'/'+folder.name]={'artifact':str(report.relative_to(R)),'sha256':sha(report),'failedKeys':[x['key']for x in rows if x['outcome']=='F'],'unassessedKeys':[x['key']for x in rows if x['outcome']=='U'],'unassessedReasons':[{'denominator':bucket,'reason':reason,'rows':n}for(bucket,reason),n in sorted(collections.Counter((x['denominator'],x['reason'])for x in rows if x['outcome']=='U').items())]}
 return {'version':1,'scope':'Command exit failures, compilation failures and independent score F/U are separate. A failed/blocked observation never automatically becomes a product/business defect. All original successful superseded Android attempts remain included.','acquisitionCommands':commands,'nonzeroAcquisitionCommands':[x for x in commands if x['exitCode']!=0],'intentionalGenericNativeFailures':generic,'repairCompilationFailures':compiles,'independentGrades':scores,'administrativeRecords':[str(p.relative_to(R))for p in sorted((R/'harness-failures').iterdir())if p.is_file()]}
def render(d):
 lines=['# 失败与未评估记录','','原始命令、图片、收据、自查和编译日志全部保留。采集失败、业务失败与未评估不是同一个概念。','',f"归档采集命令 {len(d['acquisitionCommands'])} 条（含公开集成和首次翻译尝试），非零退出 {len(d['nonzeroAcquisitionCommands'])} 条。通用工程探针另有 {len(d['intentionalGenericNativeFailures'])} 次有意缺失目标的原生非零退出。",'','## 非零采集命令','','| 记录 | 退出码 | 秒 |','| --- | ---: | ---: |']
 for x in d['nonzeroAcquisitionCommands']:lines.append(f"| [{x['artifact']}]({x['artifact']}) | {x['exitCode']} | {x['wallSeconds']:.3f} |")
 lines+=['','首次输入翻译的 iOS preflight 拒绝没有执行原生测试；同批 Android 执行成功，但其映射已废弃。这 8 次都保留并计入对应初始反馈流程，不归为组件业务缺陷。','','## 编译失败','']
 for x in d['repairCompilationFailures']:lines.append(f"- [{x['artifact']}]({x['artifact']})，JSON pointer `{x['pointer']}`；原始错误与后续编译记录在同一不可变报告内。")
 lines+=['','## 独立验收 F / U','','| 匿名报告 | F 行 | U 行 |','| --- | ---: | ---: |']
 for name,x in d['independentGrades'].items():lines.append(f"| [{name}]({x['artifact']}) | {len(x['failedKeys'])} | {len(x['unassessedKeys'])} |")
 lines+=['','完整原子 key、逐分母未评估原因与引用见 [failure-index.json](failure-index.json)。字号、padding、物理 hit 区域等运行时能力缺口继续保留；未成功派发后的回调区间不判为 handler 缺陷。修复前后同一 key 的 F→P/F/U、回归与新增可评估失败见 [result-summary.json](result-summary.json)。','','## 共同基础设施记录','']
 for rel in d['administrativeRecords']:lines.append(f'- [{rel}]({rel})')
 lines+=['','独立通用探针还保留了错误画布色预期造成的视觉失败，以及首次映射别名导致的未评估；见 [ENGINEERING.md](ENGINEERING.md) 和 [独立通用验证](independent-generic/summary.json)。这些不是 WaterRound 样本，也不计为新版工具独享收益。','']
 return '\n'.join(lines)
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();d=compute();j=R/'failure-index.json';md=R/'FAILURES.md'
 if a.write:
  assert not j.exists()and not md.exists();j.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n');md.write_text(render(d))
 else:assert read(j)==d and md.read_text()==render(d)
 print('PASS: command, compile, F and U failure inventory reproduces')
if __name__=='__main__':main()
