# Project Restructure — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor monolithic `app.py` into a modular Flask project with Blueprints per domain.

**Architecture:** Single `app/` package with `create_app()` factory, shared `db.py`, and 3 domain blueprints (`computadores`, `impressoras`, `config_ad`). Each blueprint has its own `__init__.py` (routes) and `services.py` (business logic). Templates move to `app/templates/`.

**Tech Stack:** Flask 3.x, sqlite3, ldap3, pysnmp-lextudio

## Global Constraints

- No new dependencies beyond current frozen set
- `gestao_ti.db` stays at project root for backward compatibility
- All existing routes and API signatures must remain identical
- Port 5000, debug mode on
- HTML templates are identical copies (no visual changes)

---

### Task 1: Create package structure and `app/db.py`

**Files:**
- Create: `app/__init__.py`
- Create: `app/db.py`
- Create: `app/blueprints/__init__.py`
- Create: `app/blueprints/computadores/__init__.py`
- Create: `app/blueprints/computadores/services.py`
- Create: `app/blueprints/impressoras/__init__.py`
- Create: `app/blueprints/impressoras/services.py`
- Create: `app/blueprints/config_ad/__init__.py`
- Create: `app/blueprints/config_ad/services.py`

- [ ] **Step 1: Create directory tree**

```bash
mkdir -p app/blueprints/computadores
mkdir -p app/blueprints/impressoras
mkdir -p app/blueprints/config_ad
mkdir -p app/templates
```

- [ ] **Step 2: Create `app/db.py`**

```python
import sqlite3

def get_db_connection():
    conn = sqlite3.connect('gestao_ti.db')
    conn.row_factory = sqlite3.Row
    return conn
```

- [ ] **Step 3: Create empty init files**

```python
# app/__init__.py
# (in-memory placeholder — filled in Task 8)
```

```python
# app/blueprints/__init__.py
```

- [ ] **Step 4: Create placeholder blueprint init files**

```python
# app/blueprints/computadores/__init__.py
# (filled in Task 3)
```

```python
# app/blueprints/impressoras/__init__.py
# (filled in Task 5)
```

```python
# app/blueprints/config_ad/__init__.py
# (filled in Task 7)
```

- [ ] **Step 5: Create placeholder service files**

```python
# app/blueprints/computadores/services.py
# (filled in Task 2)
```

```python
# app/blueprints/impressoras/services.py
# (filled in Task 4)
```

```python
# app/blueprints/config_ad/services.py
# (filled in Task 6)
```

- [ ] **Step 6: Verify structure**

```bash
Get-ChildItem -Recurse -Name app
```
Expected: all 9 files created.

---

### Task 2: Write `app/blueprints/computadores/services.py`

**Files:**
- Modify: `app/blueprints/computadores/services.py`

**Interfaces:**
- Consumes: from `app.db`: `get_db_connection()`
- Produces: `sync_computadores_ad(config)`, `verificar_ping(ip)`, `buscar_usuario_wmi(ip, ad_user, ad_pass)`, `verificar_status_computador(pc, ad_user, ad_pass)`

- [ ] **Step 1: Write services.py**

```python
import socket
import subprocess
from ldap3 import Server, Connection, ALL, core
from app.db import get_db_connection

PS_SCRIPT_WMI = '''
param($ip, $user, $pass)
try {
    $secpass = ConvertTo-SecureString $pass -AsPlainText -Force
    $cred = New-Object System.Management.Automation.PSCredential($user, $secpass)
    $u = Get-WmiObject -Class Win32_ComputerSystem -ComputerName $ip -Credential $cred -ErrorAction Stop
    Write-Output $u.UserName
} catch {
    try {
        $u = Get-WmiObject -Class Win32_ComputerSystem -ComputerName $ip -ErrorAction Stop
        Write-Output $u.UserName
    } catch {
        Write-Output ''
    }
}
'''

def sync_computadores_ad(config):
    target = config['ad_ip'] or config['server']
    ad_server = Server(target, get_info=ALL)
    ad_conn = Connection(ad_server, user=config['username'], password=config['password'], auto_bind=True)
    ad_conn.search(
        search_base=config['base_dn'],
        search_filter='(objectClass=computer)',
        attributes=['cn', 'dNSHostName', 'operatingSystem', 'lastLogonTimestamp']
    )
    conn_db = get_db_connection()
    conn_db.execute('DELETE FROM computadores')
    for entry in ad_conn.entries:
        nome = str(entry.cn) if hasattr(entry, 'cn') and entry.cn else ''
        hostname = str(entry.dNSHostName) if hasattr(entry, 'dNSHostName') and entry.dNSHostName else ''
        sistema = str(entry.operatingSystem) if hasattr(entry, 'operatingSystem') and entry.operatingSystem else ''
        ip = hostname if hostname and '.' in hostname else ''
        if ip:
            try:
                ip = socket.gethostbyname(hostname)
            except:
                pass
        conn_db.execute(
            'INSERT INTO computadores (nome, ip, usuario_logado, status) VALUES (?, ?, ?, ?)',
            (nome, ip, '', 'offline')
        )
    conn_db.commit()
    conn_db.close()
    ad_conn.unbind()
    return len(ad_conn.entries)

def verificar_ping(ip):
    if not ip:
        return False
    try:
        ping = subprocess.run(
            ['ping', '-n', '1', '-w', '2000', ip],
            capture_output=True, text=True, timeout=5
        )
        return ping.returncode == 0
    except:
        return False

def buscar_usuario_wmi(ip, ad_user, ad_pass):
    try:
        ps = subprocess.run(
            ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', PS_SCRIPT_WMI,
             '-ip', ip, '-user', ad_user, '-pass', ad_pass],
            capture_output=True, text=True, timeout=15
        )
        saida = ps.stdout.strip()
        if saida and 'Access Denied' not in saida and not saida.startswith('Error'):
            return saida.split('\\')[-1] if '\\' in saida else saida
    except:
        pass
    return ''

def verificar_status_computador(pc, ad_user, ad_pass):
    pc_id = pc['id']
    nome = pc['nome']
    ip = pc['ip']
    online = False
    usuario = ''
    if ip and not ip.replace('.', '').isdigit():
        try:
            ip = socket.gethostbyname(ip)
        except:
            pass
    if ip:
        online = verificar_ping(ip)
    if online and ip:
        usuario = buscar_usuario_wmi(ip, ad_user, ad_pass)
    conn_db = get_db_connection()
    conn_db.execute(
        'UPDATE computadores SET status=?, usuario_logado=?, ip=? WHERE id=?',
        ('online' if online else 'offline', usuario, ip, pc_id)
    )
    conn_db.commit()
    conn_db.close()
    return {
        'id': pc_id, 'nome': nome, 'ip': ip,
        'status': 'online' if online else 'offline',
        'usuario_logado': usuario
    }
```

---

### Task 3: Write `app/blueprints/computadores/__init__.py` (Routes)

**Files:**
- Modify: `app/blueprints/computadores/__init__.py`

**Interfaces:**
- Consumes: from `app.db`: `get_db_connection()`; from `.services`: `sync_computadores_ad()`, `verificar_status_computador()`

- [ ] **Step 1: Write computadores blueprint**

```python
from flask import Blueprint, jsonify, render_template, request
import socket
import threading
from app.db import get_db_connection
from app.blueprints.computadores.services import sync_computadores_ad, verificar_status_computador

computadores_bp = Blueprint('computadores', __name__)

@computadores_bp.route('/')
@computadores_bp.route('/computadores')
def page_computadores():
    return render_template('computadores.html')

@computadores_bp.route('/api/computadores')
def get_computadores():
    conn = get_db_connection()
    computadores = conn.execute('SELECT * FROM computadores').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in computadores])

@computadores_bp.route('/api/sync/computadores', methods=['POST'])
def sync_computadores():
    from ldap3 import core
    conn_db = get_db_connection()
    config = conn_db.execute('SELECT * FROM config_ad WHERE id=1').fetchone()
    conn_db.close()
    if not config:
        return jsonify({"status": "error", "message": "Configuração AD não encontrada"}), 400
    try:
        total = sync_computadores_ad(config)
        return jsonify({"status": "success", "message": f"Sincronizados {total} computadores do AD!"})
    except core.exceptions.LDAPBindError as e:
        return jsonify({"status": "error", "message": f"Falha na autenticação: {str(e)}"}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": f"Falha ao sincronizar: {str(e)}"}), 500

@computadores_bp.route('/api/sync/status', methods=['POST'])
def sync_status():
    conn_db = get_db_connection()
    config = conn_db.execute('SELECT * FROM config_ad WHERE id=1').fetchone()
    computadores = conn_db.execute('SELECT id, nome, ip FROM computadores').fetchall()
    conn_db.close()
    ad_user = config['username'] if config else ''
    ad_pass = config['password'] if config else ''
    resultados = []

    def verificar(pc):
        resultado = verificar_status_computador(pc, ad_user, ad_pass)
        resultados.append(resultado)

    threads = []
    for pc in computadores:
        t = threading.Thread(target=verificar, args=(pc,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    return jsonify({"status": "success", "message": f"Verificados {len(resultados)} computadores", "dados": resultados})
```

---

### Task 4: Write `app/blueprints/impressoras/services.py`

**Files:**
- Modify: `app/blueprints/impressoras/services.py`

**Interfaces:**
- Produces: `verificar_impressoras_snmp(impressoras)` → list of `(online, modelo)` tuples

- [ ] **Step 1: Write impressoras services**

```python
import asyncio
from pysnmp.hlapi.asyncio import getCmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity

async def _check_one(ip, comunidade):
    online = False
    modelo = ''
    try:
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            SnmpEngine(),
            CommunityData(comunidade),
            UdpTransportTarget((ip, 161), timeout=3, retries=1),
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0'))
        )
        if not errorIndication and not errorStatus:
            online = True
            for name, val in varBinds:
                modelo = str(val)
    except:
        pass
    return online, modelo

def verificar_impressoras_snmp(impressoras):
    async def check_all():
        return await asyncio.gather(
            *[_check_one(prt['ip'], prt['comunidade_snmp']) for prt in impressoras]
        )
    return asyncio.run(check_all())
```

---

### Task 5: Write `app/blueprints/impressoras/__init__.py` (Routes)

**Files:**
- Modify: `app/blueprints/impressoras/__init__.py`

**Interfaces:**
- Consumes: from `app.db`: `get_db_connection()`; from `.services`: `verificar_impressoras_snmp()`

- [ ] **Step 1: Write impressoras blueprint**

```python
from flask import Blueprint, jsonify, render_template, request
from datetime import datetime
from app.db import get_db_connection
from app.blueprints.impressoras.services import verificar_impressoras_snmp

impressoras_bp = Blueprint('impressoras', __name__)

@impressoras_bp.route('/impressoras')
def page_impressoras():
    return render_template('impressoras.html')

@impressoras_bp.route('/api/impressoras')
def get_impressoras():
    conn = get_db_connection()
    impressoras = conn.execute('SELECT * FROM impressoras').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in impressoras])

@impressoras_bp.route('/api/impressoras/adicionar', methods=['POST'])
def adicionar_impressora():
    dados = request.json
    nome = dados.get('nome', '').strip()
    ip = dados.get('ip', '').strip()
    comunidade = dados.get('comunidade_snmp', 'public').strip()
    if not nome or not ip:
        return jsonify({"status": "error", "message": "Nome e IP são obrigatórios"}), 400
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO impressoras (nome, ip, comunidade_snmp) VALUES (?, ?, ?)',
        (nome, ip, comunidade)
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Impressora cadastrada!"})

@impressoras_bp.route('/api/impressoras/remover/<int:id>', methods=['DELETE'])
def remover_impressora(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM impressoras WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Impressora removida!"})

@impressoras_bp.route('/api/sync/impressoras', methods=['POST'])
def sync_impressoras():
    conn_db = get_db_connection()
    impressoras = conn_db.execute('SELECT * FROM impressoras').fetchall()
    conn_db.close()
    if not impressoras:
        return jsonify({"status": "success", "message": "Nenhuma impressora cadastrada", "dados": []})
    resultados_async = verificar_impressoras_snmp(impressoras)
    resultados = []
    for idx, (online, modelo) in enumerate(resultados_async):
        prt = impressoras[idx]
        agora = datetime.now().strftime('%d/%m/%Y %H:%M')
        conn_db = get_db_connection()
        conn_db.execute(
            'UPDATE impressoras SET status=?, modelo=?, ultima_verificacao=? WHERE id=?',
            ('ok' if online else 'offline', modelo, agora, prt['id'])
        )
        conn_db.commit()
        conn_db.close()
        resultados.append({
            'id': prt['id'], 'nome': prt['nome'], 'ip': prt['ip'],
            'status': 'ok' if online else 'offline',
            'modelo': modelo, 'ultima_verificacao': agora
        })
    return jsonify({"status": "success", "message": f"Verificadas {len(resultados)} impressoras", "dados": resultados})
```

---

### Task 6: Write `app/blueprints/config_ad/services.py`

**Files:**
- Modify: `app/blueprints/config_ad/services.py`

**Interfaces:**
- Produces: `testar_conexao_ldap(server, ad_ip, base_dn, username, password)` → `(True, message)` or raises exception

- [ ] **Step 1: Write config_ad services**

```python
from ldap3 import Server, Connection, ALL

def testar_conexao_ldap(server, ad_ip, base_dn, username, password):
    target = ad_ip or server
    ad_server = Server(target, get_info=ALL)
    conn = Connection(ad_server, user=username, password=password, auto_bind=True)
    conn.unbind()
    return True, "Conectado ao AD com sucesso!"
```

---

### Task 7: Write `app/blueprints/config_ad/__init__.py` (Routes)

**Files:**
- Modify: `app/blueprints/config_ad/__init__.py`

**Interfaces:**
- Consumes: from `app.db`: `get_db_connection()`; from `.services`: `testar_conexao_ldap()`

- [ ] **Step 1: Write config_ad blueprint**

```python
from flask import Blueprint, jsonify, render_template, request
from app.db import get_db_connection
from app.blueprints.config_ad.services import testar_conexao_ldap

config_ad_bp = Blueprint('config_ad', __name__)

@config_ad_bp.route('/config')
def page_config():
    conn = get_db_connection()
    config = conn.execute('SELECT * FROM config_ad WHERE id=1').fetchone()
    conn.close()
    if config:
        return render_template('config.html', server=config['server'], ad_ip=config['ad_ip'] or '', base_dn=config['base_dn'], username=config['username'])
    return render_template('config.html', server='', ad_ip='', base_dn='', username='')

@config_ad_bp.route('/api/config')
def get_config():
    conn = get_db_connection()
    config = conn.execute('SELECT server, ad_ip, base_dn, username FROM config_ad WHERE id=1').fetchone()
    conn.close()
    if config:
        return jsonify(dict(config))
    return jsonify({})

@config_ad_bp.route('/api/config/salvar', methods=['POST'])
def salvar_config():
    dados = request.json
    conn = get_db_connection()
    conn.execute(
        'REPLACE INTO config_ad (id, server, ad_ip, base_dn, username, password) VALUES (1, ?, ?, ?, ?, ?)',
        (dados.get('server'), dados.get('ad_ip'), dados.get('base_dn'), dados.get('username'), dados.get('password'))
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Configuração salva com sucesso!"})

@config_ad_bp.route('/api/config/testar', methods=['POST'])
def testar_config():
    from ldap3 import core
    dados = request.json
    server = dados.get('server')
    ad_ip = dados.get('ad_ip')
    base_dn = dados.get('base_dn')
    username = dados.get('username')
    password = dados.get('password')
    if not all([server, base_dn, username, password]):
        return jsonify({"status": "error", "message": "Todos os campos são obrigatórios"}), 400
    try:
        ok, msg = testar_conexao_ldap(server, ad_ip, base_dn, username, password)
        return jsonify({"status": "success", "message": msg})
    except core.exceptions.LDAPBindError as e:
        return jsonify({"status": "error", "message": f"Falha na autenticação: {str(e)}"}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": f"Falha ao conectar: {str(e)}"}), 500
```

---

### Task 8: Create app factory, entry point, move templates, delete old files

**Files:**
- Modify: `app/__init__.py`
- Create: `run.py`
- Move: `computadores.html` → `app/templates/computadores.html`
- Move: `impressoras.html` → `app/templates/impressoras.html`
- Move: `config.html` → `app/templates/config.html`
- Delete: `app.py`
- Delete: `index.html`

- [ ] **Step 1: Write `app/__init__.py`**

```python
from flask import Flask

def create_app():
    app = Flask(__name__, template_folder='templates')
    from app.blueprints.computadores import computadores_bp
    from app.blueprints.impressoras import impressoras_bp
    from app.blueprints.config_ad import config_ad_bp
    app.register_blueprint(computadores_bp)
    app.register_blueprint(impressoras_bp)
    app.register_blueprint(config_ad_bp)
    return app
```

- [ ] **Step 2: Create `run.py`**

```python
from app import create_app
app = create_app()
if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

- [ ] **Step 3: Move HTML files**

```bash
Move-Item computadores.html app/templates/computadores.html
Move-Item impressoras.html app/templates/impressoras.html
Move-Item config.html app/templates/config.html
```

- [ ] **Step 4: Delete old files**

```bash
Remove-Item app.py
Remove-Item index.html
```

- [ ] **Step 5: Start app and check for import errors**

```bash
Start-Process -WindowStyle Hidden -FilePath ".venv\Scripts\python.exe" -ArgumentList "run.py" -PassThru
Start-Sleep -Seconds 3
Invoke-WebRequest -Uri "http://localhost:5000/" -UseBasicParsing
```
Expected: `200 OK`

---

### Task 9: Verify all endpoints and freeze dependencies

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: Kill existing process and start fresh**

```bash
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1
Start-Process -WindowStyle Hidden -FilePath ".venv\Scripts\python.exe" -ArgumentList "run.py" -PassThru
Start-Sleep -Seconds 3
```

- [ ] **Step 2: Check all pages load**

```bash
$pages = @('/', '/computadores', '/impressoras', '/config')
foreach ($p in $pages) {
    $r = Invoke-WebRequest -Uri "http://localhost:5000$p" -UseBasicParsing
    Write-Output "$p → $($r.StatusCode)"
}
```
Expected: all 200.

- [ ] **Step 3: Check APIs respond**

```bash
$r = Invoke-WebRequest -Uri "http://localhost:5000/api/computadores" -UseBasicParsing
$r = Invoke-WebRequest -Uri "http://localhost:5000/api/impressoras" -UseBasicParsing
$r = Invoke-WebRequest -Uri "http://localhost:5000/api/config" -UseBasicParsing
```
Expected: all 200.

- [ ] **Step 4: Freeze requirements**

```bash
.venv\Scripts\pip.exe freeze > requirements.txt
```

- [ ] **Step 5: Verify final structure**

```bash
Get-ChildItem -Recurse -Name | Where-Object { $_ -notmatch '\.venv|__pycache__|\.db$|docs/' }
```
Expected:
```
app/__init__.py
app/db.py
app/blueprints/__init__.py
app/blueprints/computadores/__init__.py
app/blueprints/computadores/services.py
app/blueprints/impressoras/__init__.py
app/blueprints/impressoras/services.py
app/blueprints/config_ad/__init__.py
app/blueprints/config_ad/services.py
app/templates/computadores.html
app/templates/impressoras.html
app/templates/config.html
run.py
setup_db.py
requirements.txt
gestao_ti.db
```
