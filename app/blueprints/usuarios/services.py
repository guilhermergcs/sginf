from ldap3 import Server, Connection, ALL, core, MODIFY_REPLACE

def _conectar(config, use_ssl=False):
    target = config['ad_ip'] or config['server']
    if use_ssl:
        ad_server = Server(target, port=636, use_ssl=True, get_info=ALL)
    else:
        ad_server = Server(target, get_info=ALL)
    ad_conn = Connection(ad_server, user=config['username'], password=config['password'], auto_bind=True)
    return ad_conn

def _set_password(config, sam_account_name, nova_senha):
    search_base = _search_base(config)
    ad_conn = _conectar(config, use_ssl=True)
    ad_conn.search(
        search_base=search_base,
        search_filter=f'(sAMAccountName={sam_account_name})',
        attributes=['distinguishedName']
    )
    if not ad_conn.entries:
        ad_conn.unbind()
        raise ValueError(f"Usuário {sam_account_name} não encontrado")
    dn = ad_conn.entries[0].entry_dn
    nova_senha_encoded = f'"{nova_senha}"'.encode('utf-16-le')
    ad_conn.modify(dn, {'unicodePwd': [(MODIFY_REPLACE, [nova_senha_encoded])]})
    ad_conn.unbind()
    target = config['ad_ip'] or config['server']
    ad_server = Server(target, get_info=ALL)
    ad_conn = Connection(ad_server, user=config['username'], password=config['password'], auto_bind=True)
    return ad_conn

def _search_base(config, default='CN=Users'):
    base_dn = config['base_dn']
    ou = config.get('ou_usuarios', default)
    if ou.lower().endswith(base_dn.lower()):
        return ou
    return f'{ou},{base_dn}'

def listar_usuarios_ad(config):
    search_base = _search_base(config)
    ad_conn = _conectar(config)
    ad_conn.search(
        search_base=search_base,
        search_filter='(objectClass=user)',
        attributes=['cn', 'sAMAccountName', 'userAccountControl', 'displayName', 'mail', 'department', 'title']
    )
    usuarios = []
    for entry in ad_conn.entries:
        nome = str(entry.cn) if hasattr(entry, 'cn') and entry.cn else ''
        login = str(entry.sAMAccountName) if hasattr(entry, 'sAMAccountName') and entry.sAMAccountName else ''
        uac = int(str(entry.userAccountControl)) if hasattr(entry, 'userAccountControl') and entry.userAccountControl else 0
        ativo = not (uac & 2)
        def _attr(e, a):
            v = getattr(e, a, None)
            return str(v) if v else ''
        usuarios.append({
            'nome': nome,
            'login': login,
            'displayName': _attr(entry, 'displayName'),
            'email': _attr(entry, 'mail'),
            'departamento': _attr(entry, 'department'),
            'cargo': _attr(entry, 'title'),
            'status': 'ativo' if ativo else 'inativo'
        })
    ad_conn.unbind()
    return usuarios

def _set_user_status(config, sam_account_name, ativo):
    search_base = _search_base(config)
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

def _update_user(config, sam_account_name, campos):
    search_base = _search_base(config)
    ad_conn = _conectar(config)
    ad_conn.search(
        search_base=search_base,
        search_filter=f'(sAMAccountName={sam_account_name})',
        attributes=['distinguishedName']
    )
    if not ad_conn.entries:
        ad_conn.unbind()
        raise ValueError(f"Usuário {sam_account_name} não encontrado")
    dn = ad_conn.entries[0].entry_dn
    mapeamento = {
        'nome': 'cn',
        'displayName': 'displayName',
        'email': 'mail',
        'departamento': 'department',
        'cargo': 'title'
    }
    modificacoes = {}
    for chave, valor in campos.items():
        attr_ad = mapeamento.get(chave)
        if attr_ad:
            modificacoes[attr_ad] = [(MODIFY_REPLACE, [valor])]
    if modificacoes:
        ad_conn.modify(dn, modificacoes)
    ad_conn.unbind()
