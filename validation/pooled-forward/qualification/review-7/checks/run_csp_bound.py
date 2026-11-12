import sys,argparse,itertools,time
sys.dont_write_bytecode=True
from encoding_cases import *
p=argparse.ArgumentParser();p.add_argument('--arm',required=True);p.add_argument('--path',required=True);a=p.parse_args();arm=Path(a.path).resolve();sys.path.insert(0,str(arm/'scripts'))
import scroll_coverage
# Nine identities, eight mutually disjoint positions; every pair must occupy
# different positions. Pigeonhole proves UNSAT independently. This deliberately
# stresses the helper's documented bounded search, not physical geometry ABI.
keys=list('ABCDEFGHI');positions={(0,2*i,1,2*i+1)for i in range(8)};registry={k:{'rectangles':positions}for k in keys};links=[{'witness_pairs':[(x,y)]}for x,y in itertools.combinations(keys,2)]
result=scroll_coverage.joint_assignment(registry,links,{})
passed=result['assignment']is None and result['visited_nodes']<=10000 and result['max_nodes']==10000 and result['status']=='search_budget_exhausted'
row={'id':'C65-default-10000-search-bound-closed','status':'P'if passed else'F','arm':a.arm,'evidence_class':'HOST synthetic helper CSP stress, no NATIVE/timing credit','independent_oracle':'9 identities cannot occupy8 pairwise-distinct boxes (pigeonhole principle)','actual':result,'scope':'Tests default budget termination and closed None result, not reachability of this arbitrary CSP under a physical native rectangle adapter.'};save(ROOT/'raw'/(a.arm+'-csp-bound-result.json'),row)
if not passed:save(ROOT/'first-failures'/(a.arm+'--csp-bound.json'),row)
print(json.dumps(row,indent=2))
