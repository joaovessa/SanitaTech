"""Extração oficial, retomável e auditável. Dados individuais ficam apenas locais."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urljoin
import argparse
import ftplib
import hashlib
import json
import re
import zipfile
import requests

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
RAW = DATA / 'raw'
OUT = DATA / 'processed'
BASE = 'https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/'
MUNICIPIO = '3513801'


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)


def status(key, **values):
    write_json(DATA / 'status' / f'{key}.json', dict(source=key, updated_at=now(), **values))


def links(url):
    response = requests.get(url, timeout=(15, 90))
    response.raise_for_status()
    return [urljoin(url, x) for x in re.findall(r'href="([^"]+)"', response.text)]


def download(url, key):
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / url.rsplit('/', 1)[-1]
    receipt = path.with_suffix(path.suffix + '.json')
    if path.exists() and receipt.exists():
        expected = json.loads(receipt.read_text(encoding='utf-8'))['sha256']
        if hashlib.file_digest(path.open('rb'), 'sha256').hexdigest() == expected:
            return path
    status(key, state='downloading', url=url, bytes=0)
    temp = path.with_suffix(path.suffix + '.part')
    digest = hashlib.sha256()
    size = 0
    if url.startswith('ftp:'):
        from urllib.parse import urlparse
        parsed = urlparse(url)
        with ftplib.FTP(parsed.hostname, timeout=90) as ftp:
            ftp.login()
            with temp.open('wb') as dest:
                def receive(chunk):
                    nonlocal size
                    dest.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
                ftp.retrbinary('RETR ' + parsed.path, receive)
    else:
        with requests.get(url, stream=True, timeout=(15, 180)) as response:
            response.raise_for_status()
            total = int(response.headers.get('Content-Length', 0))
            with temp.open('wb') as dest:
                for chunk in response.iter_content(1024 * 1024):
                    dest.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
                    status(key, state='downloading', url=url, bytes=size, total_bytes=total)
    temp.replace(path)
    write_json(receipt, dict(url=url, retrieved_at=now(), bytes=size, sha256=digest.hexdigest()))
    return path


def census_table(key, pattern):
    import pandas as pd
    candidates = [u for u in links(BASE + 'Agregados_por_Setor_csv/') if re.search(pattern, u)]
    if not candidates:
        raise ValueError('Arquivo não encontrado no catálogo oficial do IBGE.')
    path = download(sorted(candidates)[-1], key)
    status(key, state='processing', file=path.name)
    frames = []
    with zipfile.ZipFile(path) as archive:
        for member in archive.namelist():
            if not member.lower().endswith('.csv'):
                continue
            with archive.open(member) as probe:
                sample = probe.read(65536)
            try:
                sample.decode('utf-8-sig')
                encoding = 'utf-8-sig'
            except UnicodeDecodeError:
                encoding = 'latin1'
            with archive.open(member) as handle:
                for chunk in pd.read_csv(handle, sep=';', encoding=encoding, dtype=str, chunksize=30000):
                    col = next((c for c in chunk if c.upper() in ('CD_SETOR', 'COD_SETOR', 'SETOR')), None)
                    if col is None:
                        raise ValueError(f'Código do setor ausente: {list(chunk.columns)[:8]}')
                    part = chunk[chunk[col].str.startswith(MUNICIPIO, na=False)].copy()
                    if len(part):
                        frames.append(part.rename(columns={col: 'CD_SETOR'}))
    if not frames:
        raise ValueError('Nenhum setor de Diadema encontrado; revisar schema e codificação.')
    result = pd.concat(frames, ignore_index=True)
    if result.CD_SETOR.duplicated().any():
        raise ValueError('Setores duplicados: revisão necessária antes do join.')
    OUT.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT / f'{key}.csv', index=False)
    status(key, state='ready', rows=len(result), file=path.name, url=candidates[-1])


def geometry():
    import geopandas as gpd
    key = 'malha'
    urls = links(BASE + 'malha_com_atributos/setores/gpkg/UF/SP/')
    urls = [u for u in urls if u.lower().endswith(('.zip', '.gpkg'))]
    if not urls:
        raise ValueError('Malha SP não localizada no catálogo oficial.')
    path = download(sorted(urls)[-1], key)
    status(key, state='processing', file=path.name)
    source = f'/vsizip/{path.as_posix()}' if path.suffix == '.zip' else str(path)
    frame = gpd.read_file(source, where="CD_MUN = '3513801'")
    if not len(frame):
        raise ValueError('Malha de Diadema vazia.')
    if not frame.CD_SETOR.astype(str).str.startswith(MUNICIPIO).all():
        raise ValueError('Filtro municipal inválido.')
    OUT.mkdir(parents=True, exist_ok=True)
    frame.to_crs(4326).to_file(OUT / 'setores.geojson', driver='GeoJSON')
    status(key, state='ready', rows=len(frame), file=path.name, url=urls[-1])


def dictionary():
    urls = [u for u in links(BASE) if 'dicionario_de_dados' in u and u.endswith('.xlsx')]
    path = download(sorted(urls)[-1], 'dicionario')
    status('dicionario', state='ready', file=path.name, url=urls[-1])


def health(year, month):
    import pandas as pd
    from pyreaddbc import dbc2dbf
    from dbfread import DBF
    key = f'sih_{year}{month:02}'
    filename = f'RDSP{year % 100:02}{month:02}.dbc'
    url = 'ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados/' + filename
    path = download(url, key)
    status(key, state='processing', file=filename)
    dbf = path.with_suffix('.dbf')
    if not dbf.exists():
        dbc2dbf(str(path), str(dbf))
    frame = pd.DataFrame(iter(DBF(str(dbf), encoding='latin1')))
    residents = frame[frame.MUNIC_RES.astype(str).str.strip().eq('351380')].copy()
    diagnosis = residents.DIAG_PRINC.astype(str).str.strip().str.upper()
    eligible = residents[diagnosis.str.match(r'^A0[0-9]')].copy()
    # RD é por competência de processamento; não equivale a admissão no mês.
    # Cada linha é uma AIH, não uma pessoa única nem necessariamente uma internação nova.
    eligible['valor'] = pd.to_numeric(eligible.VAL_TOT.astype(str).str.replace(',', '.'), errors='coerce')
    if eligible['valor'].isna().any():
        raise ValueError('VAL_TOT inválido; custo não calculado.')
    OUT.mkdir(parents=True, exist_ok=True)
    report = dict(competencia=f'{year}-{month:02}', aih_a00_a09=len(eligible),
                  valor_pago=float(eligible.valor.sum()), aih_residentes_total=len(residents))
    write_json(OUT / f'{key}.json', report)
    # Não persistir CEP/idade/sexo no produto público.
    status(key, state='ready', rows=len(eligible), url=url, **report)


TASKS = {
    'malha': geometry,
    'basico': lambda: census_table('basico', r'/Agregados_por_setores_basico_BR.*\.zip$'),
    'saneamento': lambda: census_table('saneamento', r'/Agregados_por_setores_caracteristicas_domicilio2_BR.*\.zip$'),
    'domicilios1': lambda: census_table('domicilios1', r'/Agregados_por_setores_caracteristicas_domicilio1_BR.*\.zip$'),
    'demografia': lambda: census_table('demografia', r'/Agregados_por_setores_demografia_BR.*\.zip$'),
    'dicionario': dictionary,
}


def run(task, year=2024, month=1):
    key = f'sih_{year}{month:02}' if task == 'sih' else task
    try:
        status(key, state='starting')
        health(year, month) if task == 'sih' else TASKS[task]()
    except Exception as exc:
        status(key, state='error', error=f'{type(exc).__name__}: {exc}')
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('task', choices=[*TASKS, 'sih', 'sih-periodo', 'censo'])
    parser.add_argument('--year', type=int, choices=range(2021, 2025), default=2024)
    parser.add_argument('--month', type=int, choices=range(1, 13), default=1)
    args = parser.parse_args()
    if args.task == 'sih-periodo':
        for year in range(2021, 2025):
            for month in range(1, 13):
                key = f'sih_{year}{month:02}'
                receipt = DATA / 'status' / f'{key}.json'
                if receipt.exists() and json.loads(receipt.read_text(encoding='utf-8')).get('state') == 'ready':
                    continue
                try:
                    run('sih', year, month)
                except Exception as exc:
                    print(f'{key}: {exc}', flush=True)
    elif args.task == 'censo':
        for name in TASKS:
            try:
                run(name)
            except Exception as exc:
                print(f'{name}: {exc}', flush=True)
    else:
        run(args.task, args.year, args.month)
