from ldap3 import Server, Connection, ALL

def testar_conexao_ldap(server, ad_ip, base_dn, username, password):
    target = ad_ip or server
    ad_server = Server(target, get_info=ALL)
    conn = Connection(ad_server, user=username, password=password, auto_bind=True)
    conn.unbind()
    return True, "Conectado ao AD com sucesso!"
