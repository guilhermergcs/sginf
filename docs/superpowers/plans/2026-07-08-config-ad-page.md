# Página de Configuração do AD — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a configuration page for Active Directory with form fields and test connection functionality.

**Architecture:** Single-page form with two POST API endpoints — one to test connection via ldap3, one to persist settings to SQLite. Front-end is plain HTML+JS served by Flask.

**Tech Stack:** Flask, SQLite, ldap3, vanilla HTML/CSS/JS

## Global Constraints

- Use `.venv` virtual environment at `C:\Users\guilh\Desktop\teste\.venv`
- All Flask routes in `app.py`
- Database table `config_ad` already exists in `gestao_ti.db`
- Style: modern (background `#f5f7fa`, white card, rounded corners, shadow)
- Password field must NOT pre-fill with saved password

---

### Task 1: Dependencies and imports

**Files:**
- Modify: `app.py:1`

- [ ] **Step 1: Install ldap3**

```bash
& "C:\Users\guilh\Desktop\teste\.venv\Scripts\pip.exe" install ldap3
```

- [ ] **Step 2: Update Flask import to include `request`**

Edit `app.py` line 1:

```python
from flask import Flask, jsonify, render_template, request
```

---

### Task 2: Add test connection API route

**Files:**
- Modify: `app.py` (after line 69, before `if __name__`)

**Interfaces:**
- Produces: `POST /api/config/testar` — accepts `{ server, base_dn, username, password }`, returns `{ status: "success" }` or `{ status: "error", message: "..." }`

- [ ] **Step 1: Add the test connection route**

Insert before `if __name__ == '__main__':` (line 72):

```python
@app.route('/api/config/testar', methods=['POST'])
def testar_config():
    from ldap3 import Server, Connection, ALL, core
    dados = request.json
    server = dados.get('server')
    base_dn = dados.get('base_dn')
    username = dados.get('username')
    password = dados.get('password')

    if not all([server, base_dn, username, password]):
        return jsonify({"status": "error", "message": "Todos os campos são obrigatórios"}), 400

    try:
        ad_server = Server(server, get_info=ALL)
        conn = Connection(ad_server, user=username, password=password, auto_bind=True)
        conn.unbind()
        return jsonify({"status": "success", "message": "Conectado ao AD com sucesso!"})
    except core.exceptions.LDAPBindError as e:
        return jsonify({"status": "error", "message": f"Falha na autenticação: {str(e)}"}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": f"Falha ao conectar: {str(e)}"}), 500
```

---

### Task 3: Create config.html page

**Files:**
- Create: `config.html`

- [ ] **Step 1: Write the HTML page**

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Configuração do AD</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', system-ui, sans-serif; background: #f5f7fa; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
        .card { background: #fff; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); padding: 40px; width: 100%; max-width: 520px; }
        h1 { font-size: 22px; color: #1a1a2e; margin-bottom: 8px; }
        .subtitle { color: #6b7280; font-size: 14px; margin-bottom: 28px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; font-size: 13px; font-weight: 600; color: #374151; margin-bottom: 6px; }
        input { width: 100%; padding: 10px 14px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 14px; transition: border-color 0.15s; outline: none; }
        input:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.1); }
        .password-wrapper { position: relative; }
        .password-wrapper input { padding-right: 44px; }
        .toggle-password { position: absolute; right: 12px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; color: #9ca3af; font-size: 18px; }
        .toggle-password:hover { color: #6b7280; }
        .actions { display: flex; gap: 12px; margin-top: 28px; }
        .btn { flex: 1; padding: 11px 20px; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: opacity 0.15s; }
        .btn:hover { opacity: 0.9; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-primary { background: #3b82f6; color: #fff; }
        .btn-success { background: #10b981; color: #fff; }
        .feedback { margin-top: 16px; padding: 12px 16px; border-radius: 8px; font-size: 14px; display: none; }
        .feedback.success { display: block; background: #d1fae5; color: #065f46; border: 1px solid #a7f3d0; }
        .feedback.error { display: block; background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
        .spinner { display: none; width: 18px; height: 18px; border: 2px solid #e5e7eb; border-top-color: #3b82f6; border-radius: 50%; animation: spin 0.6s linear infinite; margin: 0 auto; }
        .spinner.visible { display: block; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .btn-loading { display: flex; align-items: center; justify-content: center; gap: 8px; }
        .btn-content { display: flex; align-items: center; justify-content: center; gap: 8px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Configuração do Active Directory</h1>
        <p class="subtitle">Configure os parâmetros de conexão com o servidor AD</p>
        <form id="config-form">
            <div class="form-group">
                <label for="server">Servidor AD</label>
                <input type="text" id="server" name="server" placeholder="dc.exemplo.local" required>
            </div>
            <div class="form-group">
                <label for="base_dn">Base DN</label>
                <input type="text" id="base_dn" name="base_dn" placeholder="dc=exemplo,dc=local" required>
            </div>
            <div class="form-group">
                <label for="username">Usuário</label>
                <input type="text" id="username" name="username" placeholder="admin@exemplo.local" required>
            </div>
            <div class="form-group">
                <label for="password">Senha</label>
                <div class="password-wrapper">
                    <input type="password" id="password" name="password" placeholder="••••••••" required>
                    <button type="button" class="toggle-password" id="toggle-password" aria-label="Mostrar senha">👁️</button>
                </div>
            </div>
            <div class="actions">
                <button type="button" class="btn btn-primary" id="btn-testar">
                    <span class="btn-content"><span class="spinner"></span><span class="btn-text">Testar Conexão</span></span>
                </button>
                <button type="submit" class="btn btn-success" id="btn-salvar">
                    <span class="btn-content"><span class="spinner"></span><span class="btn-text">Salvar</span></span>
                </button>
            </div>
            <div class="feedback" id="feedback"></div>
        </form>
    </div>
    <script>
        const server_input = document.getElementById('server');
        const base_dn_input = document.getElementById('base_dn');
        const username_input = document.getElementById('username');
        const password_input = document.getElementById('password');
        const btn_testar = document.getElementById('btn-testar');
        const form = document.getElementById('config-form');
        const feedback = document.getElementById('feedback');
        const toggle_btn = document.getElementById('toggle-password');

        // Toggle password visibility
        toggle_btn.addEventListener('click', () => {
            const type = password_input.type === 'password' ? 'text' : 'password';
            password_input.type = type;
            toggle_btn.textContent = type === 'password' ? '👁️' : '🙈';
        });

        function set_loading(btn, loading) {
            const content = btn.querySelector('.btn-content');
            const spinner = content.querySelector('.spinner');
            const text = content.querySelector('.btn-text');
            spinner.classList.toggle('visible', loading);
            btn.disabled = loading;
            text.textContent = loading ? 'Aguarde...' : btn === btn_testar ? 'Testar Conexão' : 'Salvar';
        }

        function show_feedback(message, type) {
            feedback.textContent = message;
            feedback.className = 'feedback ' + type;
        }

        // Load saved config on page load
        async function load_config() {
            try {
                const resp = await fetch('/api/config');
                const data = await resp.json();
                if (data.server) {
                    server_input.value = data.server || '';
                    base_dn_input.value = data.base_dn || '';
                    username_input.value = data.username || '';
                }
            } catch (e) { /* no saved config */ }
        }

        // Test connection
        btn_testar.addEventListener('click', async () => {
            const data = {
                server: server_input.value,
                base_dn: base_dn_input.value,
                username: username_input.value,
                password: password_input.value
            };
            set_loading(btn_testar, true);
            show_feedback('', '');
            try {
                const resp = await fetch('/api/config/testar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await resp.json();
                if (resp.ok) {
                    show_feedback(result.message, 'success');
                } else {
                    show_feedback(result.message || 'Erro ao testar conexão', 'error');
                }
            } catch (e) {
                show_feedback('Erro de rede ao testar conexão', 'error');
            } finally {
                set_loading(btn_testar, false);
            }
        });

        // Save config
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                server: server_input.value,
                base_dn: base_dn_input.value,
                username: username_input.value,
                password: password_input.value
            };
            const btn_salvar = document.getElementById('btn-salvar');
            set_loading(btn_salvar, true);
            show_feedback('', '');
            try {
                const resp = await fetch('/api/config/salvar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await resp.json();
                if (resp.ok) {
                    show_feedback(result.message, 'success');
                } else {
                    show_feedback(result.message || 'Erro ao salvar', 'error');
                }
            } catch (e) {
                show_feedback('Erro de rede ao salvar', 'error');
            } finally {
                set_loading(btn_salvar, false);
            }
        });

        load_config();
    </script>
</body>
</html>
```

---

### Task 4: Add GET /api/config route to return saved data (JSON)

**Files:**
- Modify: `app.py` (before `if __name__`)

**Note:** The existing `GET /config` route renders the HTML page. We need a JSON endpoint for the front-end to load saved config.

- [ ] **Step 1: Add JSON API route to return saved config**

Insert before `if __name__ == '__main__':`:

```python
@app.route('/api/config')
def get_config():
    conn = get_db_connection()
    config = conn.execute('SELECT server, base_dn, username FROM config_ad WHERE id=1').fetchone()
    conn.close()
    if config:
        return jsonify(dict(config))
    return jsonify({})
```
