import unittest
import material


class Material(unittest.TestCase):
    def test_whole_status_arrays_and_exact_numbers_survive(self):
        raw=b'{"assertions":[{"status":"F","actual":9007199254740993.0},{"status":"P","actual":true},{"status":"U","actual":null}],"issues":[{"message":"pending evidence"}]}'
        value=material.projection.strict_json(raw); result,proof=material.neutralize(value)
        self.assertEqual(material.projection.json_text(result),material.projection.json_text(value))
        self.assertFalse(proof['identity_metadata_changes'])

    def test_actual_path_cannot_be_rewritten(self):
        with self.assertRaises(ValueError): material.neutralize({'actual':{'path':'/Users/rex/private/value'}})

    def test_metadata_path_preserves_all_other_facts(self):
        value={'source':{'path':'/Users/rex/project/component.swift'},'assertions':[{'status':'F','expected':True,'actual':False}]}
        result,proof=material.neutralize(value,{'/Users/rex/project/component.swift':'sources/v0/0/component.swift'})
        self.assertEqual(result['source']['path'],'sources/v0/0/component.swift')
        self.assertEqual(result['assertions'],value['assertions']);self.assertEqual(len(proof['identity_metadata_changes']),1)

    def test_factual_operations_are_retained(self):
        value={'operations':[{'status':'F','actual':False}],'assertions':[]}
        result,proof=material.neutralize(value);self.assertEqual(result,value)
        self.assertNotIn('operations',proof['omitted_top_level'])

    def test_outcome_keeps_failure_and_validation_claim(self):
        value={'profile':'ios','action':'final','exit_code':1,'accepted':False,
               'error':{'type':'ValueError','message':'missing facts'},'wall_seconds':7,
               'service_output':'/Users/rex/record/engine','capture':None}
        result=material.outcome_view(value)
        self.assertEqual(result['error'],value['error']);self.assertFalse(result['accepted'])
        self.assertNotIn('wall_seconds',result)

    def test_new_data_fields_stop_outcome_projection(self):
        with self.assertRaises(ValueError):material.outcome_view({'exit_code':1,'new_assertions':[{'status':'F'}]})

    def test_metadata_cannot_conceal_new_assertion_arrays(self):
        with self.assertRaises(ValueError):material.outcome_view({'exit_code':1,'config':{'assertions':[{'status':'F'}]}})

    def test_integrity_claim_is_retained(self):
        value={'profile':'ios','integrity':{'passed':False,'error':{'type':'ValueError','message':'changed source'}}}
        self.assertEqual(material.outcome_view(value),value)


if __name__=='__main__':unittest.main(verbosity=2)
