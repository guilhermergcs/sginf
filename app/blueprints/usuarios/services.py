from ldap3 import Server, Connection, ALL, core, MODIFY_REPLACE

def _conectar(config):
    target = config['ad_ip'] or config['server']
    ad_server = Server(target, get_info=ALL)
    ad_conn = Connection(ad_server, user=config['username'], password=config['password'], auto_bind=True)
    return ad_conn

def listar_usuarios_ad(config):
    base_dn = config['base_dn']
    ou_base = config.get('ou_usuarios', 'CN=Users')
    search_base = f'{ou_base},{base_dn}'
    ad_conn = _conectar(config)
    ad_conn.search(
        search_base=search_base,
        search_filter='(objectClass=user)',
        attributes=['cn', 'sAMAccountName', 'userAccountControl']
    )
    usuarios = []
    for entry in ad_conn.entries:
        nome = str(entry.cn) if hasattr(entry, 'cn') and entry.cn else ''
        login = str(entry.sAMAccountName) if hasattr(entry, 'sAMAccountName') and entry.sAMAccountName else ''
        uac = int(str(entry.userAccountControl)) if hasattr(entry, 'userAccountControl') and entry.userAccountControl else 0
        ativo = not (uac & 2)
        usuarios.append({
            'nome': nome,
            'login': login,
            'status': 'ativo' if ativo else 'inativo'
        })
    ad_conn.unbind()
    return usuarios

def _set_user_status(config, sam_account_name, ativo):
    base_dn = config['base_dn']
    ou_base = config.get('ou_usuarios', 'CN=Users')
    search_base = f'{ou_base},{base_dn}'
    ad_conn = _conectar(config)
    ad_conn.search(
        search_base=search_base,
        search_filter=f'(sAMAccountName={sam_account_name})',
        attributes=['userAccountControl']
    )
    if not ad_conn.entries:
        ad_conn.unbind()
        raise ValueError(f"Usuário {sam_account_name} não encontrado")
    entry = ad_conn.entries[0]
    dn = entry.entry_dn
    uac = int(str(entry.userAccountControl)) if hasattr(entry, 'userAccountControl') and entry.userAccountControl else 0
    novo_uac = uac & ~2 if ativo else uac | 2
    ad_conn.modify(dn, {'userAccountControl': [(MODIFY_REPLACE, [novo_uac])]})
    ad_conn.unbind()
