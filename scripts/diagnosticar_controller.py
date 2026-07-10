import json, requests, urllib3, sys
urllib3.disable_warnings()
host = sys.argv[1]
user = sys.argv[2]
pw = sys.argv[3]
s = requests.Session(); s.verify = False
r = s.post(f'https://{host}:8443/api/login', json={'username': user, 'password': pw}, timeout=10)
if r.status_code != 200: print('Login ERRO:', r.status_code); exit()

print('=== Devices ===')
r = s.get(f'https://{host}:8443/api/s/default/stat/device', timeout=15)
if r.status_code != 200: print('ERRO:', r.status_code); exit()
data = r.json()
for d in data.get('data', [])[:5]:
    if d.get('type', '').lower() not in ('uap', 'ap'): continue
    print('---', d.get('name'), d.get('model'), '---')
    print('  num_sta global:', d.get('num_sta'))
    # Verifica se tem user_num_sta
    for f in ['user_num_sta','guest_num_sta','wifi_num_sta']:
        if f in d:
            print('  ' + f + ':', d[f])

    # VAP table
    vaps = d.get('vap_table', [])
    if vaps:
        print('  VAPs:', len(vaps))
        for v in vaps[:4]:
            print('    ssid:', v.get('essid'), 'radio:', v.get('radio'), 'num_sta:', v.get('num_sta'), 'ccq:', v.get('ccq'))
    else:
        print('  (sem vap_table)')

    print()

print('=== Clientes (stat/sta) ===')
r = s.get(f'https://{host}:8443/api/s/default/stat/sta', timeout=15)
if r.status_code == 200:
    clientes = r.json().get('data', [])
    print('  Total clientes conectados:', len(clientes))
    for c in clientes[:10]:
        print('  - hostname:', c.get('hostname',''), 'ip:', c.get('ip',''), 'radio:', c.get('radio','?'), 'signal:', c.get('signal',''), 'essid:', c.get('essid',''))
    if clientes:
        from collections import Counter
        radios = Counter(c.get('radio','?') for c in clientes)
        print('  Por radio:', dict(radios))
else:
    print('  ERRO acesso stat/sta:', r.status_code)
    r = s.get(f'https://{host}:8443/api/s/default/stat/user', timeout=15)
    if r.status_code == 200:
        clientes = r.json().get('data', [])
        print('  Total via stat/user:', len(clientes))
        for c in clientes[:5]:
            print('  - hostname:', c.get('hostname',''), 'ip:', c.get('ip',''), 'radio:', c.get('radio','?'))
    else:
        print('  ERRO stat/user:', r.status_code)
