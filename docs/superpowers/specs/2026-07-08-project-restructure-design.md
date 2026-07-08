# Project Restructure — Modular Flask with Blueprints

## Goal

Organize the monolithic `app.py` (352 lines) into a modular Flask project using Blueprints, separating routes, business logic, and templates into a clean package structure.

## Final Structure

```
teste/
├── app/
│   ├── __init__.py              # Application factory (create_app)
│   ├── db.py                    # Database connection (get_db_connection)
│   ├── blueprints/
│   │   ├── __init__.py          # Empty
│   │   ├── computadores/
│   │   │   ├── __init__.py      # Blueprint + all computador routes
│   │   │   └── services.py      # AD sync, ping, WMI user lookup
│   │   ├── impressoras/
│   │   │   ├── __init__.py      # Blueprint + all impressora routes
│   │   │   └── services.py      # SNMP query logic
│   │   └── config_ad/
│   │       ├── __init__.py      # Blueprint + all config routes
│   │       └── services.py      # LDAP connection test
│   └── templates/
│       ├── base.html            # Base layout with sidebar + CSS
│       ├── computadores.html
│       ├── impressoras.html
│       └── config.html
├── run.py                       # Entry point
├── setup_db.py                  # Kept as-is
├── requirements.txt             # Frozen dependencies
├── gestao_ti.db                 # Kept as-is
└── docs/
```

## Module Responsibilities

### `app/__init__.py`
- `create_app()` function
- Configures template folder to `app/templates`
- Registers all 3 blueprints with URL prefixes
- Registers root route `'/'` → computadores

### `app/db.py`
- `get_db_connection()` — same as current, returns `sqlite3.Connection` with `row_factory = sqlite3.Row`
- Database path derived from `app.instance_path` or current working directory

### `app/blueprints/computadores/`
- **Routes**: `/`, `/computadores`, `/api/computadores`, `/api/sync/computadores`, `/api/sync/status`
- **Services**: `sync_computadores_ad()` (LDAP query), `verificar_ping()`, `buscar_usuario_wmi()` (PowerShell + WMI)

### `app/blueprints/impressoras/`
- **Routes**: `/impressoras`, `/api/impressoras`, `/api/impressoras/adicionar`, `/api/impressoras/remover/<id>`, `/api/sync/impressoras`
- **Services**: `consultar_snmp(ip, comunidade)` — returns (online, modelo)

### `app/blueprints/config_ad/`
- **Routes**: `/config`, `/api/config`, `/api/config/salvar`, `/api/config/testar`
- **Services**: `testar_conexao_ldap(server, ad_ip, base_dn, username, password)` — returns success/error

### `run.py`
```python
from app import create_app
app = create_app()
if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

## Migration Plan

1. Create `app/` package and subdirectories
2. Copy HTML files into `app/templates/`
3. Extract `get_db_connection()` into `app/db.py`
4. Extract computador routes + services into `app/blueprints/computadores/`
5. Extract impressora routes + services into `app/blueprints/impressoras/`
6. Extract config routes + services into `app/blueprints/config_ad/`
7. Write `app/__init__.py` with `create_app()`
8. Write `run.py`
9. Verify all 3 pages load and APIs respond
10. Freeze `requirements.txt`

## Key Decisions

- **No models layer**: SQLite queries are simple enough to stay inline or in services
- **No static folder**: Current app has no CSS/JS files (styles are inline in templates)
- **No config file**: `debug=True` and `port=5000` stay in `run.py`; can extract later if needed
- **DB path**: Database stays at project root `gestao_ti.db` for backward compatibility
