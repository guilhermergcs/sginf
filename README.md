# Gerenciamento de TI

Sistema web para gerenciamento de computadores (via Active Directory + WMI) e impressoras (via SNMP).

## Funcionalidades

- **Computadores** — Sincronização com AD (LDAP), ping e usuário logado via WMI
- **Impressoras** — Cadastro manual com IP e comunidade SNMP, verificação online/modelo via SNMP
- **Configuração AD** — Teste de conexão LDAP, salvamento de credenciais

## Tecnologias

- Python 3 + Flask
- SQLite
- ldap3 (Active Directory)
- pysnmp-lextudio (SNMP)
- Bootstrap 5 (interface)

## Como rodar

```bash
.venv\Scripts\python run.py
```

Acessar em `http://localhost:5000`
