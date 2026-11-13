import re
import urllib.request

urls = [
    'https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/',
    'https://geoftp.ibge.gov.br/recortes_para_fins_estatisticos/malha_de_setores_censitarios/',
]
for url in urls:
    print(url)
    try:
        html = urllib.request.urlopen(url, timeout=40).read().decode('latin1')
        print('\n'.join(re.findall(r'href="([^"]+)"', html)))
    except Exception as exc:
        print(type(exc).__name__, str(exc))
