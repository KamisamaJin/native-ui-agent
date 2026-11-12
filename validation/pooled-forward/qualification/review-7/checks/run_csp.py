import sys,argparse,itertools,random
sys.dont_write_bytecode=True
from encoding_cases import *
p=argparse.ArgumentParser();p.add_argument('--arm',required=True);p.add_argument('--path',required=True);a=p.parse_args();arm=Path(a.path).resolve();sys.path.insert(0,str(arm/'scripts'))
import scroll_coverage
base=ROOT/'work'/a.arm/'csp';base.mkdir(parents=True);rows=[]
def separated(a,b):return a[3]<=b[1]or b[3]<=a[1]
def valid(chosen,clauses,orders):return all(any(separated(chosen[x],chosen[y])for x,y in clause)for clause in clauses)and all((chosen[x][1]<=chosen[y][1]if o<0 else chosen[x][1]>=chosen[y][1])for(x,y),o in orders.items()if o)
def exhaustive(domains,clauses,orders):
 keys=sorted(domains)
 for values in itertools.product(*(sorted(domains[k])for k in keys)):
  chosen=dict(zip(keys,values))
  if valid(chosen,clauses,orders):return chosen
 return None
def run(name,domains,clauses,orders,budget=10000,expect_budget=False):
 oracle=exhaustive(domains,clauses,orders);result=scroll_coverage.joint_assignment({k:{'rectangles':set(v)}for k,v in domains.items()},[{'witness_pairs':c}for c in clauses],orders,max_nodes=budget);assignment=result['assignment']
 passed=(assignment is not None)==(oracle is not None)and(assignment is None or valid(assignment,clauses,orders))
 if expect_budget:passed=assignment is None and result['status']=='search_budget_exhausted'and result['visited_nodes']<=budget
 row={'id':name,'status':'P'if passed else'F','arm':a.arm,'evidence_class':'HOST independent exhaustive finite CSP oracle, no image/native/runtime credit','domains':{k:sorted(v)for k,v in domains.items()},'link_clauses':clauses,'orders':[[*k,v]for k,v in orders.items()],'oracle_assignment':oracle,'actual':result,'max_nodes':budget};rows.append(row);save(base/(name+'.json'),row)
 if not passed:save(ROOT/'first-failures'/(a.arm+'--'+name+'.json'),row)

# The lexicographically first tuple overlaps; a nonminimum assignment succeeds.
domains={'A':[(0,1,1,3),(1,0,2,2)],'B':[(0,2,1,4)]};run('C01-nonminimum-choice',domains,[[('A','B')]],{('A','B'):-1});run('C02-budget-one-fails-closed',domains,[[('A','B')]],{('A','B'):-1},budget=0,expect_budget=True)
# An odd cycle requires incompatible choices across all original links jointly.
choice=[(0,0,1,1),(0,2,1,3)];run('C03-odd-cycle-unsat',{k:choice for k in'ABC'},[[('A','B')],[('B','C')],[('A','C')]],{})
run('C04-alternative-link-pairs',{'A':[(0,0,1,3)],'B':[(0,1,1,4)],'C':[(0,5,1,7)],'D':[(0,6,1,8)]},[[('A','B'),('A','C')],[('C','D'),('B','D')]],{})
rng=random.Random(720193);keys=list('ABCD');pairs=list(itertools.combinations(keys,2));rects=[(x,y,x+1,y+h)for x in[0,1]for y in range(4)for h in[1,2]]
for i in range(60):
 domains={k:rng.sample(rects,2)for k in keys};clauses=[rng.sample(pairs,rng.randrange(1,4))for _ in range(rng.randrange(1,5))];orders={pair:rng.choice([-1,1])for pair in rng.sample(pairs,rng.randrange(0,4))};run('C-random-'+str(i).zfill(2),domains,clauses,orders)
save(ROOT/'raw'/(a.arm+'-csp-results.json'),rows);print(json.dumps({'arm':a.arm,'rows':len(rows),'P':sum(r['status']=='P'for r in rows),'F':sum(r['status']=='F'for r in rows),'sat_cases':sum(r['oracle_assignment']is not None for r in rows),'max_visited_nodes':max(r['actual']['visited_nodes']for r in rows)},indent=2))
