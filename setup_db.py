from app.db import get_db_connection


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
            ou_usuarios TEXT
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


if __name__ == '__main__':
    criar_tabelas()
    print('Tabelas criadas/verificadas com sucesso.')
