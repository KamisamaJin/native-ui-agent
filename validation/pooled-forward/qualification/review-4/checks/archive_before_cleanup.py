from support import *
import fcntl,tarfile
archive_root=ROOT/'archives';archive_root.mkdir(exist_ok=False)
locks=[];roots=[];seen=set()
try:
 for cp in sorted((ROOT/'work').rglob('config.json')):
  try:config=d.load(cp)
  except Exception:continue
  if not isinstance(config,dict)or not config.get('source_roots'):continue
  raw=config.get('resources',{}).get('root')
  if not raw:continue
  root=Path(raw)
  if root in seen or not root.exists():continue
  seen.add(root)
  if not root.is_relative_to(ROOT/'work'):raise RuntimeError('Foreign root refused')
  marker=root/'owner.json';journal=root/'journal.json';lock_path=root/'lease.lock'
  if not marker.is_file()or not lock_path.is_file():continue
  identity=d.load(marker);expected=hashlib.sha256(json.dumps([str(Path(p).resolve())for p in config['source_roots']]).encode()).hexdigest()
  if identity.get('owner_key')!=expected:raise RuntimeError('Foreign owner marker refused')
  handle=lock_path.open('r+');deadline=time.monotonic()+3
  while True:
   try:fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB);break
   except BlockingIOError:
    if time.monotonic()>=deadline:handle.close();raise RuntimeError('Private root lock could not be frozen for archive')
    time.sleep(.05)
  locks.append(handle);roots.append({'root':str(root),'owner':identity,'journal_sha256':sha(journal)if journal.exists()else None})
 save(ROOT/'raw'/'pre-cleanup-archive-admission.json',{'evidence_class':'HOST','locked_positive_owned_roots':roots,'method':'Read-only OS locks freeze private resource journals during archive; no Resources entry or cleanup/native commands occurs before the archive verifies.','at_unix':time.time()})
 files=[]
 for p in sorted(ROOT.rglob('*')):
  if p.is_relative_to(archive_root):continue
  if p.is_symlink():files.append({'path':str(p.relative_to(ROOT)),'type':'symlink','target':os.readlink(p)})
  elif p.is_file():files.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size})
 manifest=save(archive_root/'PRE-CLEANUP-MANIFEST.json',{'candidate':str(CANDIDATE),'files':files,'native':False})
 archive=archive_root/'PRE-CLEANUP.tar'
 with tarfile.open(archive,'x')as tf:
  for row in files:tf.add(ROOT/row['path'],arcname=row['path'],recursive=False)
 problems=[]
 with tarfile.open(archive,'r')as tf:
  by={m.name:m for m in tf.getmembers()}
  for row in files:
   member=by[row['path']]
   if row.get('type')=='symlink':
    if not member.issym()or member.linkname!=row['target']:problems.append(row['path'])
   elif hashlib.sha256(tf.extractfile(member).read()).hexdigest()!=row['sha256']:problems.append(row['path'])
 if problems:raise RuntimeError('Pre-cleanup archive bytes differ: '+repr(problems))
 save(archive_root/'PRE-CLEANUP-SEAL.json',{'verified':True,'candidate':str(CANDIDATE),'native_runs':0,'files':[{'path':p.name,'sha256':sha(p),'bytes':p.stat().st_size}for p in [manifest,archive]],'positive_owned_roots_locked':len(roots),'at_unix':time.time()})
 print(json.dumps({'archive_verified':True,'files':len(files),'positive_owned_locks':len(roots),'archive':str(archive)},indent=2))
finally:
 for handle in reversed(locks):fcntl.flock(handle.fileno(),fcntl.LOCK_UN);handle.close()
