"""Create a private source archive from an explicit Git commit, with provenance."""
import argparse
import hashlib
import json
import io
import subprocess
import tarfile
from pathlib import Path


def create_archive(root: Path, commit: str, output: Path):
    if output.exists() or output.with_suffix('.json').exists():
        raise FileExistsError(output)
    subprocess.run(['git','archive','--format=tar',f'--output={output.resolve()}',commit],cwd=root,check=True)
    with tarfile.open(output, 'r') as archive:
        files = {}
        for member in archive.getmembers():
            if member.isfile():
                files[member.name] = hashlib.sha256(archive.extractfile(member).read()).hexdigest()
            elif not member.isdir():
                raise ValueError('Source archives must not contain links or special files')
    with tarfile.open(output, 'a') as archive:
        payload = json.dumps({'code_commit': commit, 'files': files}, sort_keys=True).encode()
        entry = tarfile.TarInfo('.source-manifest.json')
        entry.size = len(payload)
        entry.mode = 0o644
        archive.addfile(entry, io.BytesIO(payload))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if subprocess.check_output(['git','status','--porcelain'], cwd=root).strip():
        parser.error('Commit source changes before packaging; dirty releases are not reproducible')
    commit = subprocess.check_output(['git','rev-parse','HEAD'], cwd=root).decode().strip()
    if args.output.exists() or args.output.with_suffix('.json').exists():
        parser.error('Archive or metadata already exists')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    create_archive(root, commit, args.output)
    metadata = {'code_commit':commit, 'archive_sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),
                'models_included':False, 'private_data_included':False, 'official_acceptance':False}
    args.output.with_suffix('.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    print(args.output)


if __name__ == '__main__':
    main()
