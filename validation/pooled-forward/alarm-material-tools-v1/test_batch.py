import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import batch


class Reader:
    def __init__(self): self.reads=[]
    def read_bytes(self,p): self.reads.append(str(p));return Path(p).read_bytes()
    def read_json(self,p):return batch.strict_json(self.read_bytes(p))
    def hash(self,p):return hashlib.sha256(self.read_bytes(p)).hexdigest()
    def directory(self,p):return Path(p)


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(batch.encoded(value));path.chmod(0o444)
    return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def cause_index(root):
    rows=[]
    for i in range(1,6):
        for version in ['I','X','Y']:
            group='Case0%d-%s'%(i,version);seals={}
            for judge in ['J1','J2']:
                folder=root/group/judge
                grade=put(folder/'grade.json',{'anonymous_group':group,'judge_id':judge})
                seals[judge]=put(folder/'SEAL.json',{'version':1,'kind':'independent-blind-cause-grade-seal',
                    'anonymous_group':group,'judge_id':judge,'files':{'grade.json':grade['sha256']}})
            inp=put(root/group/'input.json',{'kind':'anonymous-fixed-version-input-seal','anonymous_group':group})
            end=put(root/group/'END.json',{'anonymous_group':group,'grade_seals':seals})
            rows.append({'group':group,'actors':{j:'/root/synthetic_'+group+'_'+j for j in ['J1','J2']},
                         'fork_turns':'none','model_override':None,'inputs':[inp],'episode_end':end,'seals':seals})
    return put(root/'INDEX.json',{'version':1,'kind':'global-independent-cause-grade-barrier','groups':rows,
                                 'review_record_barrier_closed':True,'product_quality_verified':False})


class Batch(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name).resolve();self.reader=Reader()
    def tearDown(self):self.temp.cleanup()

    def test_partial_cause_barrier_stops_before_data_or_output(self):
        index=put(self.root/'partial.json',{'version':1,'kind':'global-independent-cause-grade-barrier','groups':[]})
        missing={'path':str(self.root/'DO-NOT-READ-NATIVE.json'),'sha256':'0'*64}
        with self.assertRaises(ValueError):batch.prepare(self.root,self.reader,index,missing,missing,self.root/'out',self.root/'work')
        self.assertEqual(self.reader.reads,[index['path']]);self.assertFalse((self.root/'out').exists())

    def test_bad_last_role_stops_before_native_metadata(self):
        index=cause_index(self.root/'roles');body=self.reader.read_json(index['path'])
        body['groups'][-1]['seals']['J2']['sha256']='0'*64
        other=put(self.root/'bad-last.json',body);self.reader.reads=[]
        missing={'path':str(self.root/'DO-NOT-READ-NATIVE.json'),'sha256':'0'*64}
        with self.assertRaises(ValueError):batch.prepare(self.root,self.reader,other,missing,missing,self.root/'out',self.root/'work')
        self.assertNotIn(missing['path'],self.reader.reads);self.assertFalse((self.root/'out').exists())

    def test_closed_cause_records_allow_only_next_pinned_metadata(self):
        index=cause_index(self.root/'roles');native=put(self.root/'NATIVE.json',{'synthetic':True})
        bad=dict(native,sha256='0'*64)
        with self.assertRaises(ValueError):batch.prepare(self.root,self.reader,index,bad,bad,self.root/'out',self.root/'work')
        self.assertIn(native['path'],self.reader.reads)
        self.assertFalse(any('MAPPING.json' in p for p in self.reader.reads));self.assertFalse((self.root/'out').exists())

    def test_identical_initial_roots_have_separate_exact_source_aliases(self):
        work=self.root/'work';work.mkdir();source=self.root/'preserved.swift';source.write_bytes(b'original source\n')
        h=hashlib.sha256(source.read_bytes()).hexdigest();files={'0/Component.swift':{'sha256':h,'bytes':len(source.read_bytes())}}
        content=hashlib.sha256(batch.json_text(files,sort_keys=True).encode()).hexdigest()
        group=batch.Group(self.root,self.reader,'Case01-I','T1','I',{},[],{}, {},work)
        candidates={('0/Component.swift',h,len(source.read_bytes())):source}
        required={'content_sha256':content,'files':files}
        group.sources(required,[str(self.root/'A')],candidates);group.sources(required,[str(self.root/'B')],candidates)
        self.assertEqual(group.aliases[content][str(self.root/'A/Component.swift')],'sources/v0/0/Component.swift')
        self.assertEqual(group.aliases[content][str(self.root/'B/Component.swift')],'sources/v0/0/Component.swift')
        self.assertEqual(len(group.documents),1)


if __name__=='__main__':unittest.main(verbosity=2)
