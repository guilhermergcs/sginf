# Gerenciamento de TI

Sistema web para gerenciamento de computadores (via Active Directory + WMI), impressoras (via SNMP) e dispositivos de rede Wi-Fi.

## Funcionalidades

- **Computadores** — Sincronização com AD (LDAP), ping e usuário logado via WMI
- **Impressoras** — Cadastro manual com IP e comunidade SNMP, verificação online/modelo via SNMP
- **Dispositivos Wi-Fi** — Consulta de clientes via SNMP + API UniFi
- **Configuração AD** — Teste de conexão LDAP, gerenciamento de credenciais

## Tecnologias

- Python 3 + Flask (Gunicorn)
- SQLite
- ldap3 (Active Directory)
- pysnmp (SNMP)
- Bootstrap 5 (interface)

## Desenvolvimento

```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
set SECRET_KEY=dev-key-mude-isso
.venv\Scripts\python run.py
```

Acessar em `http://localhost:5000`

## Produção (Docker)

### Servidor Ubuntu (manual)

```bash
sudo bash scripts/setup_ubuntu.sh
```

O script instala Docker, clona o repositório e inicia o container.

### CI/CD (GitHub Actions)

No push para `main`:

1. **Test** — roda `pytest`
2. **Build & Push** — constrói imagem e publica no GitHub Container Registry
3. **Deploy** — via SSH no servidor (opcional)

Para habilitar o deploy automático:

1. Crie um **Deploy Key** (SSH) ou Personal Access Token no GitHub com acesso de leitura ao repositório
2. Adicione os **secrets** no repositório:
   - `SSH_HOST` — IP ou hostname do servidor
   - `SSH_USER` — usuário com permissão Docker
   - `SSH_PRIVATE_KEY` — chave privada SSH
3. Crie uma **variable** no repositório:
   - `SSH_DEPLOY_ENABLED` = `true`

### Variáveis de ambiente

| Variável | Obrigatório | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `SECRET_KEY` | Sim | — | Chave para assinar JWT (32+ hex) |
| `DATABASE_PATH` | Não | `/app/data/gestao_ti.db` | Caminho do SQLite |
| `TELEGRAM_BOT_TOKEN` | Não | — | Token do bot Telegram |
| `COOKIE_SECURE` | Não | `true` | `false` para HTTP sem TLS |
| `PORT` | Não | `5000` | Porta de exposição |
