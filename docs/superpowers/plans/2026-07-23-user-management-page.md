# User Management Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform `/register` from a single registration form into a full user management page with list, search, create, edit, and delete for `usuarios_sistema` table.

**Architecture:** 3 new REST endpoints in `auth/routes.py` (GET list, PUT update, DELETE delete). Frontend in `register.html` uses a table + single shared modal (create/edit mode). Pagination/filter utilities reused from `base.html`.

**Tech Stack:** Flask, SQLite, vanilla JS, CSS from `style.css`.

## Global Constraints

- All new endpoints protected by `@require_admin`
- DELETE blocks self-deletion (id == g.current_user['id'])
- PUT only updates password if field is non-empty string
- Frontend English variable names consistent with existing JS in `/usuarios`

---

### Task 1: Backend — API Endpoints for System Users

**Files:**
- Modify: `app/blueprints/auth/routes.py` — add 3 endpoints after `api_register()` (line 107)

**Interfaces:**
- Produces: `GET /api/auth/usuarios-sistema` → JSON array of users; `PUT /api/auth/usuarios-sistema/<id>` → `{'ok': True}`; `DELETE /api/auth/usuarios-sistema/<id>` → `{'ok': True}`

- [ ] **Step 1: Add GET list endpoint**

Insert after line 107 (`api_register` function ends):

```python
@auth_bp.route('/api/auth/usuarios-sistema')
@require_admin
def api_list_usuarios_sistema():
    conn = get_db_connection()
    users = conn.execute('''
        SELECT u.id, u.username, u.tipo, u.telegram_linked, u.created_at,
               (SELECT COUNT(*) FROM webauthn_credentials w WHERE w.user_id = u.id) as webauthn_count
        FROM usuarios_sistema u
        ORDER BY u.username
    ''').fetchall()
    conn.close()
    return jsonify([dict(u) for u in users])
```

- [ ] **Step 2: Add PUT update endpoint**

```python
@auth_bp.route('/api/auth/usuarios-sistema/<int:id>', methods=['PUT'])
@require_admin
def api_update_usuario_sistema(id):
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    tipo = data.get('tipo', 'admin')
    new_password = data.get('password', '').strip()
    if not username or len(username) < 3:
        return jsonify({'ok': False, 'error': 'Username deve ter ao menos 3 caracteres'}), 400
    conn = get_db_connection()
    existing = conn.execute('SELECT id FROM usuarios_sistema WHERE username = ? AND id != ?',
                           (username, id)).fetchone()
    if existing:
        conn.close()
        return jsonify({'ok': False, 'error': 'Username ja existe'}), 409
    if new_password:
        if len(new_password) < 4:
            conn.close()
            return jsonify({'ok': False, 'error': 'Senha deve ter ao menos 4 caracteres'}), 400
        pw_hash = generate_password_hash(new_password)
        conn.execute('UPDATE usuarios_sistema SET username = ?, tipo = ?, senha_hash = ? WHERE id = ?',
                    (username, tipo, pw_hash, id))
    else:
        conn.execute('UPDATE usuarios_sistema SET username = ?, tipo = ? WHERE id = ?',
                    (username, tipo, id))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})
```

- [ ] **Step 3: Add DELETE endpoint**

```python
@auth_bp.route('/api/auth/usuarios-sistema/<int:id>', methods=['DELETE'])
@require_admin
def api_delete_usuario_sistema(id):
    if id == g.current_user['id']:
        return jsonify({'ok': False, 'error': 'Nao pode excluir a si mesmo'}), 400
    conn = get_db_connection()
    conn.execute('DELETE FROM usuarios_sistema WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})
```

- [ ] **Step 4: Verify backend**

Start the Flask app and test with curl or browser:
```bash
curl -X GET http://localhost:5000/api/auth/usuarios-sistema  # should list users or return 401
```

Expected: Returns JSON array or 401 redirect (if not logged in).

---

### Task 2: Frontend — Rewrite register.html

**Files:**
- Rewrite: `app/templates/register.html`

**Interfaces:**
- Consumes: `GET /api/auth/usuarios-sistema`, `POST /api/auth/register`, `PUT /api/auth/usuarios-sistema/<id>`, `DELETE /api/auth/usuarios-sistema/<id>`
- Reuses: `confirmDialog()`, `getCookie()`, `filterTable()`, `initPagination()`, `applyPagination()` from base.html

- [ ] **Step 1: Write the complete HTML template**

Replace entire content of `register.html`:

```html
{% extends "base.html" %}
{% block title %}Usuários do Sistema{% endblock %}
{% block nav_register %}active{% endblock %}
{% block content %}
<div class="page-header">
  <h2>Usuários do Sistema</h2>
  <p>Gerenciamento de contas com acesso ao painel administrativo</p>
</div>

<div class="toolbar">
  <button class="btn btn-success" id="btn-novo"><svg class="icon-lg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg> Novo Usuário</button>
  <span class="status-msg" id="sync-status"></span>
  <input type="text" class="search-input" placeholder="Buscar usuário..." oninput="filterTable('tab-users', this.value)" aria-label="Buscar usuário">
</div>

<div class="card">
  <div class="card-header"><h3>Usuários Cadastrados</h3></div>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th onclick="sortTable('tab-users',0)" aria-sort="none">Usuário</th>
          <th onclick="sortTable('tab-users',1)" aria-sort="none">Tipo</th>
          <th onclick="sortTable('tab-users',2)" aria-sort="none">Telegram</th>
          <th onclick="sortTable('tab-users',3)" aria-sort="none">WebAuthn</th>
          <th onclick="sortTable('tab-users',4)" aria-sort="none">Criado em</th>
          <th>Ações</th>
        </tr>
      </thead>
      <tbody id="tab-users">
        <tr><td colspan="6" class="loading"><span class="spinner"></span>Carregando...</td></tr>
      </tbody>
    </table>
  </div>
  <div id="tab-users-pagination"></div>
</div>

<dialog id="user-dialog" class="dialog">
  <div class="dialog-body">
    <h3 class="dialog-title" id="user-dialog-title">Novo Usuário</h3>
    <div class="form-group">
      <label for="user-username">Nome de usuário</label>
      <input type="text" id="user-username" class="form-control" required minlength="3" autofocus>
    </div>
    <div class="form-group">
      <label for="user-tipo">Tipo</label>
      <select id="user-tipo" class="form-control">
        <option value="admin">Administrador</option>
      </select>
    </div>
    <div class="form-group" id="user-password-group">
      <label for="user-password">Senha</label>
      <input type="password" id="user-password" class="form-control" minlength="4">
      <small class="form-hint" id="password-hint">Mínimo 4 caracteres</small>
    </div>
    <div class="form-group" id="user-confirm-group">
      <label for="user-confirm">Confirmar senha</label>
      <input type="password" id="user-confirm" class="form-control">
    </div>
    <p class="dialog-message" id="user-feedback"></p>
    <div class="dialog-actions">
      <button class="btn btn-secondary" id="user-cancel" autofocus>Cancelar</button>
      <button class="btn btn-primary" id="user-ok">Salvar</button>
    </div>
  </div>
</dialog>
{% endblock %}
{% block scripts %}
<script>
let editUserId = null;

async function loadUsers() {
  const tbody = document.getElementById('tab-users');
  try {
    const r = await fetch('/api/auth/usuarios-sistema');
    if (!r.ok) throw new Error('Erro ao carregar');
    const users = await r.json();
    tbody.innerHTML = users.map(u => {
      const tel = u.telegram_linked ? '<span class="badge badge-success">Sim</span>' : '<span class="badge badge-secondary">Não</span>';
      const wa = u.webauthn_count > 0 ? `<span class="badge badge-info">${u.webauthn_count}</span>` : '<span class="badge badge-secondary">0</span>';
      const date = u.created_at ? new Date(u.created_at + 'Z').toLocaleDateString('pt-BR') : '-';
      return `<tr>
        <td>${esc(u.username)}</td>
        <td><span class="badge badge-primary">${esc(u.tipo)}</span></td>
        <td>${tel}</td>
        <td>${wa}</td>
        <td>${date}</td>
        <td class="actions">
          <button class="btn btn-sm btn-secondary" onclick="editUser(${u.id})" aria-label="Editar"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button>
          <button class="btn btn-sm btn-danger" onclick="deleteUser(${u.id},'${esc(u.username)}')" aria-label="Excluir"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg></button>
        </td>
      </tr>`;
    }).join('');
    if (users.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="loading">Nenhum usuário cadastrado</td></tr>';
    }
    initPagination('tab-users', 25);
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6" class="loading loading-error">${esc(e.message)}</td></tr>`;
  }
}

function esc(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function openModal(title, username, tipo, editId) {
  editUserId = editId || null;
  document.getElementById('user-dialog-title').textContent = title;
  document.getElementById('user-username').value = username || '';
  document.getElementById('user-tipo').value = tipo || 'admin';
  document.getElementById('user-password').value = '';
  document.getElementById('user-confirm').value = '';
  document.getElementById('user-feedback').textContent = '';
  document.getElementById('user-feedback').className = 'dialog-message';
  document.getElementById('user-ok').textContent = editId ? 'Atualizar' : 'Salvar';

  const pwGroup = document.getElementById('user-password-group');
  const confirmGroup = document.getElementById('user-confirm-group');
  const hint = document.getElementById('password-hint');
  if (editId) {
    pwGroup.style.display = 'block';
    confirmGroup.style.display = 'block';
    hint.textContent = 'Deixe em branco para manter a atual';
    document.getElementById('user-password').required = false;
  } else {
    pwGroup.style.display = 'block';
    confirmGroup.style.display = 'block';
    hint.textContent = 'Mínimo 4 caracteres';
    document.getElementById('user-password').required = true;
  }
  document.getElementById('user-dialog').showModal();
}

document.getElementById('btn-novo').addEventListener('click', () => openModal('Novo Usuário', '', 'admin', null));

document.getElementById('user-cancel').addEventListener('click', () => document.getElementById('user-dialog').close());

document.getElementById('user-ok').addEventListener('click', async () => {
  const username = document.getElementById('user-username').value.trim();
  const tipo = document.getElementById('user-tipo').value;
  const password = document.getElementById('user-password').value;
  const confirm = document.getElementById('user-confirm').value;
  const feedback = document.getElementById('user-feedback');

  if (!username || username.length < 3) {
    feedback.className = 'dialog-message error';
    feedback.textContent = 'Usuário deve ter ao menos 3 caracteres';
    return;
  }

  if (editUserId) {
    if (password && password !== confirm) {
      feedback.className = 'dialog-message error';
      feedback.textContent = 'Senhas não conferem';
      return;
    }
    if (password && password.length < 4) {
      feedback.className = 'dialog-message error';
      feedback.textContent = 'Senha deve ter ao menos 4 caracteres';
      return;
    }
    const r = await fetch(`/api/auth/usuarios-sistema/${editUserId}`, {
      method: 'PUT',
      headers: {'Content-Type': 'application/json', 'X-CSRF-Token': getCookie('csrf_token')},
      body: JSON.stringify({username, tipo, password}),
    });
    const res = await r.json();
    if (r.ok) {
      document.getElementById('user-dialog').close();
      loadUsers();
    } else {
      feedback.className = 'dialog-message error';
      feedback.textContent = res.error;
    }
  } else {
    if (!password || password.length < 4) {
      feedback.className = 'dialog-message error';
      feedback.textContent = 'Senha deve ter ao menos 4 caracteres';
      return;
    }
    if (password !== confirm) {
      feedback.className = 'dialog-message error';
      feedback.textContent = 'Senhas não conferem';
      return;
    }
    const r = await fetch('/api/auth/register', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-CSRF-Token': getCookie('csrf_token')},
      body: JSON.stringify({username, password, tipo}),
    });
    const res = await r.json();
    if (r.ok) {
      document.getElementById('user-dialog').close();
      loadUsers();
    } else {
      feedback.className = 'dialog-message error';
      feedback.textContent = res.error;
    }
  }
});

async function editUser(id) {
  try {
    const r = await fetch('/api/auth/usuarios-sistema');
    const users = await r.json();
    const u = users.find(x => x.id === id);
    if (u) openModal('Editar Usuário', u.username, u.tipo, id);
  } catch (e) {
    showStatus(e.message, false);
  }
}

async function deleteUser(id, username) {
  const ok = await confirmDialog(`Excluir usuário <strong>${esc(username)}</strong>?`);
  if (!ok) return;
  try {
    const r = await fetch(`/api/auth/usuarios-sistema/${id}`, {
      method: 'DELETE',
      headers: {'X-CSRF-Token': getCookie('csrf_token')},
    });
    const res = await r.json();
    if (r.ok) {
      loadUsers();
    } else {
      showStatus(res.error, false);
    }
  } catch (e) {
    showStatus(e.message, false);
  }
}

document.addEventListener('DOMContentLoaded', loadUsers);
</script>
{% endblock %}
```

This overwrites the entire file content.

- [ ] **Step 2: Verify frontend loads**

Start the Flask app, log in as admin, navigate to `/register`. Expected: table loads with user list, "Novo Usuário" button opens modal, create/edit/delete work.

- [ ] **Step 3: Verify delete protection**

Try to delete yourself (the currently logged-in user). Expected: error message "Nao pode excluir a si mesmo".

- [ ] **Step 4: Commit**

```bash
git add app/blueprints/auth/routes.py app/templates/register.html
git commit -m "feat: transform /register into full user management page"
```
