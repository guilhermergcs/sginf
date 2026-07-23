# Gerenciamento de Usuários do Sistema — Página /register

## Objetivo

Transformar a página `/register` (atualmente apenas um formulário de cadastro) em
uma página completa de gerenciamento de usuários do sistema (tabela `usuarios_sistema`),
com listagem, busca, criação, edição e exclusão.

## Backend — Novos Endpoints (auth routes)

Prefix: `/api/auth/usuarios-sistema`

### GET /api/auth/usuarios-sistema
Retorna JSON array de todos os usuários do sistema:
```json
[
  {
    "id": 1,
    "username": "admin",
    "tipo": "admin",
    "telegram_linked": 0,
    "webauthn_count": 2,
    "created_at": "2026-01-01 12:00:00"
  }
]
```
Usa subquery `SELECT COUNT(*) FROM webauthn_credentials WHERE user_id = u.id`
para popular `webauthn_count`.

Protegido por `@require_admin`.

### PUT /api/auth/usuarios-sistema/<int:id>
Body:
```json
{
  "username": "novo_nome",
  "tipo": "admin",
  "password": "nova_senha"  // opcional — só altera se preenchido
}
```
- Valida se username já existe (excluindo o próprio ID)
- Se `password` for string não-vazia, faz hash e atualiza `senha_hash`
- Protegido por `@require_admin`

### DELETE /api/auth/usuarios-sistema/<int:id>
- Bloqueia auto-exclusão (se id == g.current_user['id'], retorna erro 400)
- Protegido por `@require_admin`

## Frontend — register.html

Substituir conteúdo atual por:

### Estrutura
- `{% block nav_register %}active{% endblock %}`, `{% block main_class %}main{% endblock %}`
- `page-header` com título "Usuários do Sistema" e subtítulo
- Toolbar: botão "Novo Usuário" (abre modal no modo criação) + campo de busca
- Card com `table-wrap` > tabela > thead + tbody
- Paginação reutilizando `initPagination`/`applyPagination` da base

### Colunas da Tabela
1. **Usuário** — username
2. **Tipo** — admin (badge)
3. **Telegram** — "Sim" / "Não" conforme `telegram_linked`
4. **WebAuthn** — número de credenciais cadastradas
5. **Ações** — ícone editar + ícone excluir

### Modal Único (Criar / Editar)
`<dialog id="user-dialog" class="dialog">`

- **Título**: "Novo Usuário" ou "Editar Usuário"
- Campos comuns:
  - **Username** (input text, required, minlength 3)
  - **Tipo** (select: admin)
  - **Senha** (input password) — no **modo criar**: obrigatório, com confirmação (segundo campo). No **modo editar**: opcional, tooltip "Deixe em branco para manter a atual"
- Botão: "Salvar" (modo criar) / "Atualizar" (modo editar)
- Mensagem de feedback inline

### Ações por Linha
- **Editar** — abre modal preenchido com dados da linha, modo edição
- **Excluir** — abre `confirmDialog` da base, se confirmado faz DELETE e recarrega tabela

### Comportamento
- Ao carregar a página, faz `fetch('/api/auth/usuarios-sistema')` e popula a tabela
- Após criar/editar/excluir, recarrega a lista
- Busca filtra pelo username (client-side via `filterTable`)

## Dependências
- Nenhuma nova dependência Python
- Reutiliza `confirmDialog`, `getCookie`, `filterTable`, `initPagination` da `base.html`
- Reutiliza classes CSS existentes (`table`, `.table-wrap`, `.dialog`, `.form-group`, `.actions`, `.search-input`, `.btn`, etc.)
