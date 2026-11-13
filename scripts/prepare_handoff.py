"""Prepara uma fotografia publicável dos dados, sem copiar microdados de saúde."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
stamp = datetime.now(timezone.utc).isoformat()
provenance = DATA / 'provenance'
reference = DATA / 'reference'
provenance.mkdir(parents=True, exist_ok=True)
reference.mkdir(parents=True, exist_ok=True)
entries = []
for path in sorted((DATA / 'processed').iterdir()):
    if path.suffix not in ('.csv', '.geojson', '.json'):
        continue
    key = 'malha' if path.name == 'setores.geojson' else path.stem
    state_path = DATA / 'status' / f'{key}.json'
    state = json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {}
    if state.get('state') != 'ready':
        continue
    url = state.get('url')
    receipt = next((p for p in (DATA / 'raw').glob('*.json')
                    if json.loads(p.read_text(encoding='utf-8')).get('url') == url), None)
    if receipt:
        shutil.copy2(receipt, provenance / receipt.name)
    entries.append(dict(path=path.relative_to(ROOT).as_posix(), bytes=path.stat().st_size,
                        sha256=hashlib.sha256(path.read_bytes()).hexdigest(), status=state))
for path in (DATA / 'raw').glob('dicionario*.xlsx'):
    shutil.copy2(path, reference / path.name)
    entries.append(dict(path=(reference / path.name).relative_to(ROOT).as_posix(),
                        bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    receipt = path.with_suffix(path.suffix + '.json')
    if receipt.exists():
        shutil.copy2(receipt, provenance / receipt.name)
health = [e for e in entries if '/sih_' in e['path']]
manifest = dict(snapshot_at_utc=stamp, health_coverage='Parcial; RD-SP por competência de processamento',
                health_completed_competencies=[e['status']['competencia'] for e in health],
                health_expected_competencies=48, files=entries)
(provenance / 'snapshot.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(dict(snapshot=stamp, files=len(entries), health_competencies=len(health)), ensure_ascii=False))
