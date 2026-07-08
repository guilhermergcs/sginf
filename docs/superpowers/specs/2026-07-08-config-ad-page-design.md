# Página de Configuração do AD — Design Document

## Objetivo
Criar uma página web para configuração da conexão com Active Directory, com formulário para servidor, Base DN, usuário e senha, e funcionalidade de teste de conexão.

## Rotas Back-end

### `GET /config`
Renderiza `config.html` com dados já salvos (se existirem) preenchendo o formulário.

### `POST /api/config/salvar`
Salva os dados de configuração no banco SQLite (tabela `config_ad`).
- **Body:** `{ server, base_dn, username, password }`
- **Resposta:** `{ status: "success", message: "..." }`

### `POST /api/config/testar`
Testa a conexão com o servidor AD usando os dados fornecidos (sem salvar).
- **Body:** `{ server, base_dn, username, password }`
- **Resposta sucesso:** `{ status: "success", message: "Conectado ao AD com sucesso" }`
- **Resposta erro:** `{ status: "error", message: "Falha ao conectar: <detalhes>" }`

## Front-end

### Página (`config.html`)
Layout moderno com card centralizado, campos organizados em grid, e feedback visual de teste.

**Campos:**
- Servidor AD (input text)
- Base DN (input text)
- Usuário (input text)
- Senha (input password com toggle de visibilidade)

**Botões:**
- "Testar Conexão" — envia POST para `/api/config/testar`
- "Salvar" — envia POST para `/api/config/salvar`

**Feedback:**
- Área de mensagem abaixo dos botões — verde para sucesso, vermelho para erro
- Loading spinner durante requisições

**Estilo:**
- Background cinza claro (`#f5f7fa`)
- Card branco com border-radius e box-shadow
- Campos com borda sutil e padding confortável
- Botões com cores distintas (azul para teste, verde para salvar)
- Ícone/exemplo no preview da senha

## Banco de Dados
Tabela `config_ad` já existe com colunas: id, server, base_dn, username, password.

## Considerações
- Senha do AD NÃO deve ser exibida no campo ao carregar a página
- Botão "Testar Conexão" só testa, não persiste dados
- Teste usa ldap3 (Python) — dependência do lado servidor
