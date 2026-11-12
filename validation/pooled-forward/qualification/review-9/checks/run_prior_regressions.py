from pathlib import Path
file=Path(__file__).with_name('run_typed_and_regressions.py');typed_text=file.read_text();prefix=typed_text.split('# Relevant prior certificate/domain regressions,')[0];exec(compile(prefix,str(file),'exec'))
body=typed_text.split('def regression(name,o,s,n,t):',1)[1].split("for name in['original-PNG16-rejected'",1)[0];exec(compile('def regression(name,o,s,n,t):'+body,str(file),'exec'))
tail="folder=base/'native-width-stays-strict'"+typed_text.split("folder=base/'native-width-stays-strict'",1)[1];exec(compile(tail,str(file),'exec'))
