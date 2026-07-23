import secrets
from werkzeug.security import generate_password_hash
from app.db import get_db_connection


def criar_admin_padrao():
    conn = get_db_connection()
    existing = conn.execute('SELECT id FROM usuarios_sistema LIMIT 1').fetchone()
    if existing:
        conn.close()
        return
    password = secrets.token_urlsafe(12)
    hash = generate_password_hash(password)
    conn.execute(
        'INSERT INTO usuarios_sistema (username, senha_hash, tipo) VALUES (?, ?, ?)',
        ('admin', hash, 'admin')
    )
    conn.commit()
    conn.close()
    print(f'[!] Nenhum admin encontrado. Criado usuario padrao:')
    print(f'    Usuario: admin')
    print(f'    Senha:   {password}')
    print(f'    [!] Altere a senha apos o primeiro login.')


def criar_tabelas():
    conn = get_db_connection()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS computadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            ip TEXT,
            usuario_logado TEXT,
            status TEXT DEFAULT 'offline'
        );

        CREATE TABLE IF NOT EXISTS impressoras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            ip TEXT,
            comunidade_snmp TEXT,
            modelo TEXT,
            status TEXT,
            ultima_verificacao TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS config_ad (
            id INTEGER PRIMARY KEY CHECK(id = 1),
            server TEXT,
            ad_ip TEXT,
            base_dn TEXT,
            username TEXT,
            password TEXT,
            ou_usuarios TEXT,
            ou_computadores TEXT
        );

        CREATE TABLE IF NOT EXISTS usuarios_sistema (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            tipo TEXT DEFAULT 'admin',
            telegram_id INTEGER,
            telegram_linked INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS webauthn_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES usuarios_sistema(id) ON DELETE CASCADE,
            credential_id TEXT UNIQUE NOT NULL,
            public_key TEXT NOT NULL,
            sign_count INTEGER DEFAULT 0,
            name TEXT DEFAULT 'Windows Hello',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS auth_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            user_id INTEGER REFERENCES usuarios_sistema(id),
            telegram_chat_id INTEGER,
            purpose TEXT NOT NULL CHECK(purpose IN ('telegram_link', 'telegram_login')),
            consumed INTEGER DEFAULT 0,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS dispositivos_wifi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            ip TEXT,
            comunidade_snmp TEXT,
            modelo TEXT,
            clientes_2g INTEGER DEFAULT 0,
            clientes_5g INTEGER DEFAULT 0,
            clientes_6g INTEGER DEFAULT 0,
            clientes_total INTEGER DEFAULT 0,
            status TEXT DEFAULT 'offline',
            ultima_verificacao TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS config_unifi (
            id INTEGER PRIMARY KEY CHECK(id = 1),
            host TEXT,
            username TEXT,
            password TEXT
        );
    ''')
    conn.commit()
    conn.close()


def migrar():
    criar_tabelas()
    conn = get_db_connection()
    try:
        conn.execute("ALTER TABLE config_ad ADD COLUMN ou_computadores TEXT")
        conn.commit()
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE usuarios_sistema ADD COLUMN avatar TEXT")
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()
    criar_admin_padrao()


if __name__ == '__main__':
    criar_tabelas()
    criar_admin_padrao()
    print('Tabelas criadas/verificadas com sucesso.')
