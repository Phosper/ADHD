"""Cross-platform launch with frozen dependencies already installed."""
import argparse
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--real', action='store_true')
    parser.add_argument('--port', type=int, default=18080)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    if not (root / 'apps/web/dist/index.html').is_file():
        parser.error('Build the browser app first: npm ci && npm run build in apps/web')
    os.environ['ZHIYU_MODE'] = 'real' if args.real else 'mock'
    os.environ['ZHIYU_VOICE_ENABLED'] = '1' if args.real else '0'
    import uvicorn
    uvicorn.run('services.api.app:create_app',factory=True,host='127.0.0.1',port=args.port)


if __name__ == '__main__':
    main()
