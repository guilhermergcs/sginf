import sqlite3

def conectar():
    return sqlite3.connect('gestao_ti.db')

def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    # 1. Tabela de Usuários do Sistema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios_sistema (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            tipo TEXT DEFAULT 'admin'
        )
    ''')

    # 2. Tabela de Computadores (Gerenciados)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS computadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            ip TEXT,
            usuario_logado TEXT,
            status TEXT DEFAULT 'offline'
        )
    ''')

    # 3. Tabela de Impressoras
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS impressoras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            status STRING DEFAULT 'ok'
        )
    ''')

    conn.commit()
    conn.close()
    print("Banco de dados e tabelas criados com sucesso!")

if __name__ == '__main__':
    criar_tabelas()

    # ... código anterior ...

    # 4. Tabela de Impressoras (Monitoramento SNMP)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS impressoras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            status STRING DEFAULT 'ok'
        )
    ''')

    # 5. Tabela de Configuração do AD
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config_ad (
            id INTEGER PRIMARY KEY,
            server TEXT,          -- Servidor do AD (ex: dc.suaempresa.local)
            base_dn TEXT,         -- Base Distinguished Name (ex: dc=suaempresa,dc=local)
            username TEXT,        -- Usuário do AD (comum: admin)
            password TEXT         -- Senha do AD
        )
    ''')

    # 6. Tabela de Dispositivos Wi-Fi (Ubiquiti UniFi)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dispositivos_wifi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            ip TEXT NOT NULL,
            comunidade_snmp TEXT DEFAULT 'public',
            modelo TEXT DEFAULT '',
            clientes_2g INTEGER DEFAULT 0,
            clientes_5g INTEGER DEFAULT 0,
            clientes_total INTEGER DEFAULT 0,
            status TEXT DEFAULT 'offline',
            ultima_verificacao TEXT DEFAULT ''
        )
    ''')

    # 7. Tabela de Configuração do UniFi Controller
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config_unifi (
            id INTEGER PRIMARY KEY,
            host TEXT DEFAULT '',
            username TEXT DEFAULT '',
            password TEXT DEFAULT ''
        )
    ''')

    conn.commit()
    conn.close()
    print("Banco de dados atualizado com tabela de configuração!")