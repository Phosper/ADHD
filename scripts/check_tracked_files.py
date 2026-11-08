"""Prevent common accidental publication of private runtime assets; not a full secret audit."""
import re
import subprocess
from pathlib import Path


def main():
    root=Path(__file__).resolve().parents[1]
    paths=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
    denied=[]
    private={'runtime','models','backups','artifacts','vendor'}
    suffixes={'.pem','.key','.sqlite','.sqlite3','.db','.wav','.mp3','.flac','.safetensors','.onnx','.pt','.xlsx','.xls'}
    for name in filter(None,paths):
        p=Path(name)
        if p.parts[0] in private or (p.parts[0]=='data' and p.name not in ('.gitignore','README.md')):
            denied.append(name)
        elif p.suffix.lower() in suffixes or (p.name.startswith('.env') and p.name!='.env.example'):
            denied.append(name)
        elif (root/p).is_file():
            body=(root/p).read_bytes()
            if re.search(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',body):
                denied.append(name)
    if denied:
        print('Private or credential files tracked:',*denied,sep='\n')
        raise SystemExit(1)
    print('Tracked file policy passed; this is not a comprehensive secret audit')


if __name__=='__main__':
    main()
