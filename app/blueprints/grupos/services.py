from ldap3 import MODIFY_ADD, MODIFY_DELETE, MODIFY_REPLACE

def _conectar(config):
    from ldap3 import Server, Connection, ALL
    target = config['ad_ip'] or config['server']
    ad_server = Server(target, get_info=ALL)
    ad_conn = Connection(ad_server, user=config['username'], password=config['password'], auto_bind=True)
    return ad_conn

def _grupos_ou(config):
    return f'OU=ManagedGroups,{config["base_dn"]}'

def listar_grupos_ad(config):
    target_ou = _grupos_ou(config)
    ad_conn = _conectar(config)
    ad_conn.search(
        search_base=target_ou,
        search_filter='(objectClass=group)',
        attributes=['cn', 'description', 'member']
    )
    grupos = []
    for entry in ad_conn.entries:
        grupos.append({
            'cn': str(entry.cn) if entry.cn else '',
            'description': str(entry.description) if hasattr(entry, 'description') and entry.description else '',
            'member_count': len(entry.member) if hasattr(entry, 'member') and entry.member else 0
        })
    ad_conn.unbind()
    return grupos

def listar_membros_grupo(config, group_cn):
    target_ou = _grupos_ou(config)
    ad_conn = _conectar(config)
    ad_conn.search(
        search_base=target_ou,
        search_filter=f'(cn={group_cn})',
        attributes=['cn', 'member']
    )
    if not ad_conn.entries:
        ad_conn.unbind()
        raise ValueError(f'Grupo {group_cn} não encontrado')
    entry = ad_conn.entries[0]
    member_dns = entry.member if hasattr(entry, 'member') and entry.member else []
    membros = []
    for dn in member_dns:
        dn_str = str(dn)
        ad_conn.search(
            search_base=config['base_dn'],
            search_filter=f'(distinguishedName={dn_str})',
            attributes=['cn', 'sAMAccountName']
        )
        if ad_conn.entries:
            m = ad_conn.entries[0]
            membros.append({
                'dn': dn_str,
                'cn': str(m.cn) if m.cn else dn_str.split(',')[0].split('=')[1] if '=' in dn_str else dn_str,
                'sAMAccountName': str(m.sAMAccountName) if hasattr(m, 'sAMAccountName') and m.sAMAccountName else ''
            })
        else:
            membros.append({
                'dn': dn_str,
                'cn': dn_str.split(',')[0].split('=')[1] if '=' in dn_str else dn_str,
                'sAMAccountName': ''
            })
    ad_conn.unbind()
    return membros

def adicionar_membro_grupo(config, group_cn, user_login):
    target_ou = _grupos_ou(config)
    ad_conn = _conectar(config)
    ad_conn.search(
        search_base=target_ou,
        search_filter=f'(cn={group_cn})',
        attributes=['distinguishedName']
    )
    if not ad_conn.entries:
        ad_conn.unbind()
        raise ValueError(f'Grupo {group_cn} não encontrado')
    group_dn = ad_conn.entries[0].entry_dn
    ad_conn.search(
        search_base=config['base_dn'],
        search_filter=f'(sAMAccountName={user_login})',
        attributes=['distinguishedName']
    )
    if not ad_conn.entries:
        ad_conn.unbind()
        raise ValueError(f'Usuário {user_login} não encontrado')
    user_dn = ad_conn.entries[0].entry_dn
    ad_conn.modify(group_dn, {'member': [(MODIFY_ADD, [user_dn])]})
    if ad_conn.result['description'] != 'success':
        error_msg = ad_conn.result.get('message', 'erro desconhecido')
        ad_conn.unbind()
        raise Exception(f'Falha ao adicionar membro: {error_msg}')
    ad_conn.unbind()

def remover_membro_grupo(config, group_cn, user_login):
    target_ou = _grupos_ou(config)
    ad_conn = _conectar(config)
    ad_conn.search(
        search_base=target_ou,
        search_filter=f'(cn={group_cn})',
        attributes=['distinguishedName']
    )
    if not ad_conn.entries:
        ad_conn.unbind()
        raise ValueError(f'Grupo {group_cn} não encontrado')
    group_dn = ad_conn.entries[0].entry_dn
    ad_conn.search(
        search_base=config['base_dn'],
        search_filter=f'(sAMAccountName={user_login})',
        attributes=['distinguishedName']
    )
    if not ad_conn.entries:
        ad_conn.unbind()
        raise ValueError(f'Usuário {user_login} não encontrado')
    user_dn = ad_conn.entries[0].entry_dn
    ad_conn.modify(group_dn, {'member': [(MODIFY_DELETE, [user_dn])]})
    if ad_conn.result['description'] != 'success':
        error_msg = ad_conn.result.get('message', 'erro desconhecido')
        ad_conn.unbind()
        raise Exception(f'Falha ao remover membro: {error_msg}')
    ad_conn.unbind()

def _create_group(config, cn, description=''):
    target_ou = _grupos_ou(config)
    dn = f'CN={cn},{target_ou}'
    ad_conn = _conectar(config)
    attrs = {
        'cn': cn,
        'sAMAccountName': cn,
        'objectClass': ['top', 'group'],
        'groupType': -2147483646,
    }
    if description:
        attrs['description'] = description
    ad_conn.add(dn, attrs.pop('objectClass'), attrs)
    if ad_conn.result['description'] != 'success':
        msg = ad_conn.result.get('message', 'erro desconhecido')
        ad_conn.unbind()
        raise Exception(f'Falha ao criar grupo: {msg}')
    ad_conn.unbind()
    return cn

def _update_group(config, group_cn, novo_cn='', description=''):
    target_ou = _grupos_ou(config)
    ad_conn = _conectar(config)
    ad_conn.search(
        search_base=target_ou,
        search_filter=f'(cn={group_cn})',
        attributes=['distinguishedName', 'cn']
    )
    if not ad_conn.entries:
        ad_conn.unbind()
        raise ValueError(f'Grupo {group_cn} não encontrado')
    dn = ad_conn.entries[0].entry_dn
    modificacoes = {}
    if description:
        modificacoes['description'] = [(MODIFY_REPLACE, [description])]
    if novo_cn and novo_cn != group_cn:
        ad_conn.modify_dn(dn, novo_cn)
        dn = f'CN={novo_cn},{target_ou}'
        modificacoes['sAMAccountName'] = [(MODIFY_REPLACE, [novo_cn])]
    if modificacoes:
        ad_conn.modify(dn, modificacoes)
    ad_conn.unbind()

def _delete_group(config, group_cn):
    target_ou = _grupos_ou(config)
    ad_conn = _conectar(config)
    ad_conn.search(
        search_base=target_ou,
        search_filter=f'(cn={group_cn})',
        attributes=['distinguishedName']
    )
    if not ad_conn.entries:
        ad_conn.unbind()
        raise ValueError(f'Grupo {group_cn} não encontrado')
    dn = ad_conn.entries[0].entry_dn
    ad_conn.delete(dn)
    if ad_conn.result['description'] != 'success':
        msg = ad_conn.result.get('message', 'erro desconhecido')
        ad_conn.unbind()
        raise Exception(f'Falha ao excluir grupo: {msg}')
    ad_conn.unbind()
