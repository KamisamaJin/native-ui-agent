from support import *
import fcntl,tarfile
archive_root=ROOT/'archives';archive_root.mkdir(exist_ok=False);held=[];roots=[];seen=set()
try:
 for cp in sorted(ROOT.rglob('config.json')):
  if cp.is_relative_to(archive_root):continue
  try:c=d.load(cp)
  except Exception:continue
  if not isinstance(c,dict)or not c.get('source_roots'):continue
  raw=c.get('resources',{}).get('root')
  if not raw:continue
  root=Path(raw)
  if root in seen or not root.exists():continue
  seen.add(root)
  if not root.is_relative_to(ROOT):raise RuntimeError('Foreign cleanup/archive root')
  marker=root/'owner.json';lockfile=root/'lease.lock'
  if not marker.is_file()or not lockfile.is_file():continue
  identity=d.load(marker);owner=hashlib.sha256(json.dumps([str(Path(p).resolve())for p in c['source_roots']]).encode()).hexdigest()
  if identity.get('owner_key')!=owner:raise RuntimeError('Foreign owner marker')
  stream=lockfile.open('r+');deadline=time.monotonic()+3
  while True:
   try:fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB);break
   except BlockingIOError:
    if time.monotonic()>=deadline:stream.close();raise RuntimeError('Own archive lease unavailable')
    time.sleep(.05)
  held.append(stream);roots.append({'root':str(root),'owner':identity})
 save(ROOT/'raw'/'pre-cleanup-archive-admission.json',{'evidence_class':'HOST','positive_owned_locked_roots':roots,'native_runs':0,'method':'Read-only locks freeze only private resource journals; both initial and absolute-interpreter probe roots are archived before cleanup.'})
 rows=[]
 for p in sorted(ROOT.rglob('*')):
  if p.is_relative_to(archive_root):continue
  if p.is_symlink():rows.append({'path':str(p.relative_to(ROOT)),'type':'symlink','target':os.readlink(p)})
  elif p.is_file():rows.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size})
 manifest=save(archive_root/'PRE-CLEANUP-MANIFEST.json',{'candidate':str(CANDIDATE),'native':False,'files':rows});archive=archive_root/'PRE-CLEANUP.tar'
 with tarfile.open(archive,'x')as tf:
  for row in rows:tf.add(ROOT/row['path'],arcname=row['path'],recursive=False)
 bad=[]
 with tarfile.open(archive,'r')as tf:
  by={m.name:m for m in tf.getmembers()}
  for row in rows:
   m=by[row['path']]
   if row.get('type')=='symlink':
    if not m.issym()or m.linkname!=row['target']:bad.append(row['path'])
   elif hashlib.sha256(tf.extractfile(m).read()).hexdigest()!=row['sha256']:bad.append(row['path'])
 if bad:raise RuntimeError('Archive byte mismatch '+repr(bad))
 save(archive_root/'PRE-CLEANUP-SEAL.json',{'verified':True,'positive_owned_locked_roots':len(roots),'files':[{'path':p.name,'sha256':sha(p),'bytes':p.stat().st_size}for p in [manifest,archive]],'native_runs':0,'at_unix':time.time()})
 print(json.dumps({'archive_verified':True,'archived_files':len(rows),'positive_owned_locks':len(roots)},indent=2))
finally:
 for stream in reversed(held):fcntl.flock(stream.fileno(),fcntl.LOCK_UN);stream.close()
