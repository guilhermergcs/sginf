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
