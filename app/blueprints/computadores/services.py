import re
import socket
import struct
import random
import subprocess
from ldap3 import Server, Connection, ALL, core
from app.db import get_db_connection


def _dns_lookup(hostname, dns_server):
    """DNS A-record query via UDP to a specific DNS server."""
    tid = random.randrange(0, 65536)
    labels = hostname.encode('ascii', errors='replace').split(b'.')
    qname = b''.join(bytes([len(l)]) + l for l in labels) + b'\x00'
    query = struct.pack('>HHHHHH', tid, 0x0100, 1, 0, 0, 0) + qname + struct.pack('>HH', 1, 1)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(3)
    try:
        sock.sendto(query, (dns_server, 53))
        data, _ = sock.recvfrom(1024)
    except:
        return None
    finally:
        sock.close()
    flags = struct.unpack('>H', data[2:4])[0]
    if flags & 0x000f:
        return None
    ancount = struct.unpack('>H', data[6:8])[0]
    if ancount == 0:
        return None
    pos = 12 + len(qname) + 4
    for _ in range(ancount):
        while pos < len(data):
            if data[pos] & 0xc0 == 0xc0:
                pos += 2
                break
            elif data[pos] == 0:
                pos += 1
                break
            else:
                pos += data[pos] + 1
        if pos + 10 > len(data):
            break
        rtype, _, _, rdlen = struct.unpack('>HHIH', data[pos:pos+10])
        pos += 10
        if rtype == 1 and pos + 4 <= len(data):
            ip = socket.inet_ntoa(data[pos:pos+4])
            if ip != dns_server:
                return ip
        pos += rdlen
    return None


def _nmblookup(hostname):
    """Resolve NetBIOS name (short computer name) via nmblookup."""
    try:
        out = subprocess.run(
            ['nmblookup', hostname.split('.')[0]],
            capture_output=True, text=True, timeout=5
        ).stdout
        for line in out.splitlines():
            m = re.match(r'^\s*(\d+\.\d+\.\d+\.\d+)\s', line)
            if m:
                return m.group(1)
    except:
        pass
    return None


def _resolver(hostname, dns_server=None):
    if not hostname:
        return None
    short = hostname.split('.')[0]
    candidates = set()
    # system DNS
    try:
        candidates.add(socket.gethostbyname(hostname))
    except:
        pass
    try:
        candidates.add(socket.gethostbyname(short))
    except:
        pass
    # nslookup fallback
    if dns_server:
        try:
            out = subprocess.run(
                ['nslookup', hostname, dns_server],
                capture_output=True, text=True, timeout=5
            ).stdout
            for line in out.splitlines():
                m = re.search(r'Address:\s*(\d+\.\d+\.\d+\.\d+)', line)
                if m and m.group(1) != dns_server:
                    candidates.add(m.group(1))
        except:
            pass
    # raw DNS query
    if dns_server:
        ip = _dns_lookup(hostname, dns_server)
        if ip:
            candidates.add(ip)
    # nmblookup
    ip = _nmblookup(hostname)
    if ip:
        candidates.add(ip)
    # remove the DNS server IP itself if it sneaks in
    candidates.discard(dns_server)
    return next(iter(candidates), None)

PS_SCRIPT_WMI = '''
$ip = '_IP_'
$user = '_USER_'
$pass = '_PASS_'
try {
    $secpass = ConvertTo-SecureString $pass -AsPlainText -Force
    $cred = New-Object System.Management.Automation.PSCredential($user, $secpass)
    $loggedOn = Get-WmiObject -Class Win32_LoggedOnUser -ComputerName $ip -Credential $cred -ErrorAction Stop
    $sessions = Get-WmiObject -Query "SELECT * FROM Win32_LogonSession WHERE LogonType = 2 OR LogonType = 10" -ComputerName $ip -Credential $cred -ErrorAction Stop
    $adDomain = ($user -split '\\')[0]
    $users = @()
    foreach ($session in $sessions) {
        $related = $loggedOn | Where-Object { $_.Dependent -match "LogonId=\""$($session.LogonId)\""" }
        foreach ($rel in $related) {
            if ($rel.Antecedent -match 'Domain="([^"]+)".*Name="([^"]+)"') {
                $d = $matches[1]
                $n = $matches[2]
                if ($d -eq $adDomain) {
                    $users += $d + '\' + $n
                }
            }
        }
    }
    if ($users.Count -gt 0) {
        Write-Output (($users | Select-Object -Unique) -join '; ')
    } else {
        $u = Get-WmiObject -Class Win32_ComputerSystem -ComputerName $ip -Credential $cred -ErrorAction Stop
        Write-Output $u.UserName
    }
} catch {
    try {
        $u = Get-WmiObject -Class Win32_ComputerSystem -ComputerName $ip -Credential $cred -ErrorAction Stop
        Write-Output $u.UserName
    } catch {
        try {
            $u = Get-WmiObject -Class Win32_ComputerSystem -ComputerName $ip
            Write-Output $u.UserName
        } catch {
            Write-Output ''
        }
    }
}
'''

def sync_computadores_ad(config):
    target = config['ad_ip'] or config['server']
    dns_server = config['ad_ip'] or config['server']
    ad_server = Server(target, get_info=ALL)
    ad_conn = Connection(ad_server, user=config['username'], password=config['password'], auto_bind=True)
    search_base = config.get('ou_computadores') or config['base_dn']
    ad_conn.search(
        search_base=search_base,
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
        resolved = _resolver(ip, dns_server) if ip else None
        if resolved:
            ip = resolved
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
    import sys
    if sys.platform == 'win32':
        try:
            ping = subprocess.run(
                ['ping', '-n', '1', '-w', '2000', ip],
                capture_output=True, text=True, timeout=5
            )
            return ping.returncode == 0
        except:
            return False
    targets = [ip]
    if '.' in ip and not ip.replace('.', '').isdigit():
        targets.append(ip.split('.')[0])
    for tgt in targets:
        try:
            ping = subprocess.run(
                ['ping', '-c', '1', '-W', '2', tgt],
                capture_output=True, text=True, timeout=5
            )
            if ping.returncode == 0:
                return True
        except:
            pass
        for port in (445, 135):
            try:
                with socket.create_connection((tgt, port), timeout=3):
                    return True
            except:
                pass
    return False

def buscar_usuario_wmi(ip, ad_user, ad_pass):
    try:
        def esc(s):
            return s.replace("'", "''")
        script = PS_SCRIPT_WMI.replace('_IP_', esc(ip)).replace('_USER_', esc(ad_user)).replace('_PASS_', esc(ad_pass))
        ps = subprocess.run(
            ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', script],
            capture_output=True, text=True, timeout=15
        )
        saida = ps.stdout.strip()
        if saida and 'Access Denied' not in saida and not saida.startswith('Error'):
            if '; ' in saida:
                return saida
            return saida.split('\\')[-1] if '\\' in saida else saida
    except:
        pass
    return ''

def verificar_status_computador(pc, ad_user, ad_pass, dns_server=None):
    pc_id = pc['id']
    nome = pc['nome']
    ip = pc['ip']
    online = False
    usuario = ''
    if ip and not ip.replace('.', '').isdigit():
        resolved = _resolver(ip, dns_server)
        if resolved:
            ip = resolved
    if not ip or not ip.replace('.', '').isdigit():
        hostname = pc.get('nome', '')
        resolved = _resolver(hostname, dns_server)
        if resolved:
            ip = resolved
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
