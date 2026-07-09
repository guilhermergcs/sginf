---
name: Gestão TI
description: Painel administrativo para gerenciamento de infraestrutura de TI
colors:
  azul-noite-profunda: "#1a1a2e"
  azul-noite-hover: "#16213e"
  azul-noite-ativo: "#0f3460"
  azul-tecnico: "#3b82f6"
  azul-tecnico-claro: "#60a5fa"
  cinza-sistema: "#f0f2f5"
  branco-painel: "#ffffff"
  texto-primario: "#1f2937"
  texto-secundario: "#6b7280"
  borda-fina: "#e5e7eb"
  verde-status: "#059669"
  verde-hover: "#047857"
  vermelho-status: "#dc2626"
  vermelho-hover: "#b91c1c"
  azul-hover: "#2563eb"
  amarelo-hover: "#b45309"
  label-cor: "#374151"
  th-bg: "#fafafa"
  tr-hover: "#f9fafb"
  td-border: "#f3f4f6"
  feedback-success-bg: "#d1fae5"
  feedback-success-text: "#065f46"
  feedback-success-border: "#a7f3d0"
  feedback-error-bg: "#fee2e2"
  feedback-error-text: "#991b1b"
  feedback-error-border: "#fecaca"
  toggle-password-cor: "#9ca3af"
typography:
  display:
    fontFamily: "'Segoe UI', system-ui, -apple-system, sans-serif"
    fontSize: "clamp(1.25rem, 4vw, 1.375rem)"
    fontWeight: 700
    lineHeight: 1.2
  headline:
    fontFamily: "'Segoe UI', system-ui, -apple-system, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 700
    lineHeight: 1.3
  title:
    fontFamily: "'Segoe UI', system-ui, -apple-system, sans-serif"
    fontSize: "0.938rem"
    fontWeight: 600
    lineHeight: 1.4
  body:
    fontFamily: "'Segoe UI', system-ui, -apple-system, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "'Segoe UI', system-ui, -apple-system, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0.04em"
    textTransform: "uppercase"
rounded:
  sm: "6px"
  md: "8px"
  lg: "10px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "20px"
  xl: "24px"
  xxl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.azul-tecnico}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "8px 18px"
    fontWeight: 600
  button-primary-hover:
    backgroundColor: "{colors.azul-hover}"
  button-success:
    backgroundColor: "{colors.verde-status}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "8px 18px"
  button-success-hover:
    backgroundColor: "{colors.verde-hover}"
  button-danger:
    backgroundColor: "{colors.vermelho-status}"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "5px 12px"
    fontSize: "0.75rem"
  button-danger-hover:
    backgroundColor: "{colors.vermelho-hover}"
  button-warning:
    backgroundColor: "#d97706"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "5px 12px"
    fontSize: "0.75rem"
  button-warning-hover:
    backgroundColor: "{colors.amarelo-hover}"
  card:
    backgroundColor: "{colors.branco-painel}"
    rounded: "{rounded.lg}"
  input:
    backgroundColor: "{colors.branco-painel}"
    textColor: "{colors.texto-primario}"
    rounded: "{rounded.md}"
    padding: "10px 14px"
    border: "1px solid {colors.borda-fina}"
---

# Design System: Gestão TI

## 1. Overview

**Creative North Star: "A Central de Comando"**

Este é o painel de controle do administrador de TI — um ambiente preciso, técnico e confiável onde cada elemento existe para tornar o monitoramento da infraestrutura mais rápido e claro. A estética é de uma central de operações: limpa, organizada, sem condecoração. O admin chega, lê o estado da rede em um relance e age.

A paleta é intencionalmente contida: um fundo cinza claro para destacar os dados, sidebar escura que ancora a navegação, e um azul técnico reservado exclusivamente para ações e estados ativos. Indicadores de status (verde/vermelho) são os elementos de maior contraste — propositalmente, já que são a informação mais crítica.

**Key Characteristics:**
- Preciso: dados técnicos apresentados de forma direta, sem ruído visual
- Consistente: cada página segue os mesmos padrões de layout e interação
- Ágil: feedback imediato para toda ação do usuário
- Sóbrio: zero decoração — cores e espaçamentos têm função

## 2. Colors

A paleta é enxuta e funcional: tons neutros no fundo e superfícies, um azul técnico para ações, e cores semânticas (verde/vermelho) para o que realmente importa — o status dos ativos.

### Primary

- **Azul Técnico** (#3b82f6): Ação primária (botões, links). Usado exclusivamente para interação, nunca como decoração.
- **Azul Técnico Claro** (#60a5fa): Estado ativo da navegação na sidebar.

### Neutral

- **Azul-Noite Profunda** (#1a1a2e): Fundo da sidebar — ancora a navegação com peso visual.
- **Azul-Noite Hover** (#16213e): Hover dos itens da sidebar.
- **Azul-Noite Ativo** (#0f3460): Estado ativo do item de navegação.
- **Cinza Sistema** (#f0f2f5): Fundo da página — superfície de baixo contraste que destaca os cards brancos.
- **Branco Painel** (#ffffff): Superfícies de conteúdo (cards, formulários).
- **Texto Primário** (#1f2937): Corpo do texto, cabeçalhos.
- **Texto Secundário** (#6b7280): Texto de apoio, placeholders, metadados.
- **Borda Fina** (#e5e7eb): Separação entre elementos (bordas de tabela, card-header, inputs).

### Semantic

- **Verde Status** (#059669): Online, ativo, ok.
- **Verde Hover** (#047857): Hover de botão success e ações de ativar.
- **Vermelho Status** (#dc2626): Offline, inativo, erro.
- **Vermelho Hover** (#b91c1c): Hover de botão danger e ações destrutivas.
- **Azul Hover** (#2563eb): Hover do botão primário (Azul Técnico).
- **Amarelo Hover** (#b45309): Hover do botão de warning.
- **Label Cor** (#374151): Cor do label de formulário (destinta do Texto Secundário porque tem peso 600).
- **TH Bg** (#fafafa): Fundo sutil do cabeçalho de tabela (mais claro que Cinza Sistema).
- **TR Hover** (#f9fafb): Hover de linhas de tabela — quase imperceptível, só o suficiente para guiar o olho horizontalmente.
- **TD Border** (#f3f4f6): Borda inferior de células de tabela — mais clara que Borda Fina para não competir com o cabeçalho.
- **Feedback Success Bg** (#d1fae5), **Feedback Success Text** (#065f46), **Feedback Success Border** (#a7f3d0): Caixa de feedback de sucesso.
- **Feedback Error Bg** (#fee2e2), **Feedback Error Text** (#991b1b), **Feedback Error Border** (#fecaca): Caixa de feedback de erro.
- **Toggle Password Cor** (#9ca3af): Cor do ícone de toggle de senha no estado padrão. Muda para Texto Secundário no hover.

### Named Rules

**A Regra do Azul Técnico.** O azul de acento aparece exclusivamente em ações primárias (botões) e no estado ativo da navegação. Nunca é usado decorativamente — sua presença sempre sinaliza interação possível.

**A Regra do Status em Tempo Real.** Verde e vermelho são os únicos pontos de alta saturação no sistema. Eles existem para serem lidos em 200ms. Nunca usar verde ou vermelho para função não relacionada a status.

## 3. Typography

**Display / Body / Label Font:** Segoe UI, system-ui, -apple-system, sans-serif (single stack)

**Character:** Uma única família sans-serif moderna e legível. Sem contraste tipográfico — a hierarquia é construída por peso (400/600/700) e tamanho, não por troca de fontes. O resultado é limpo, previsível e técnico.

### Hierarchy

- **Display** (700, clamp(1.25rem, 4vw, 1.375rem), 1.2): Nome do sistema na sidebar. Letras pequenas o bastante para não competir com o conteúdo.
- **Headline** (700, 1.375rem, 1.3): Título da página (ex: "Computadores", "Impressoras").
- **Title** (600, 0.938rem, 1.4): Cabeçalhos de card e seção.
- **Body** (400, 0.875rem, 1.5): Conteúdo principal — células de tabela, descrições, labels de formulário.
- **Label** (600, 0.75rem, 1.3, 0.04em tracking, uppercase): Cabeçalhos de coluna, subtítulo da sidebar, metadados.

## 4. Elevation

O sistema usa sombras sutis e consistentes para elevar superfícies de conteúdo (cards) acima do fundo cinza. O resultado é uma hierarquia visual clara sem profundidade exagerada — a Central de Comando é plana por padrão.

### Shadow Vocabulary

- **Card Shadow** (`box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)`): Aplicada a todos os cards e estatísticas. Sutil o bastante para não distrair, presente o bastante para separar superfícies.

### Named Rules

**A Regra da Sombra Única.** Todas as superfícies elevadas usam exatamente a mesma sombra. Não há hierarquia de elevação — cards, modais e estatísticas compartilham o mesmo tratamento.

## 5. Components

### Buttons

- **Shape:** Cantos suavemente arredondados (8px).
- **Primary (Azul Técnico #3b82f6 → #2563eb hover):** Ação principal. Padding 8px 18px, fonte 0.875rem/600. Usado para sincronizar, carregar, testar conexão.
- **Success (Verde #059669 → #047857 hover):** Ação de adição/criação. Mesmo padding e proporção do primary.
- **Danger (Vermelho #dc2626 → #b91c1c hover):** Ação destrutiva (remover). Versão small: 5px 12px, fonte 0.75rem.
- **Loading state:** Botão desabilitado com spinner substituto. Texto troca para "Aguarde...".
- **Todos os botões têm `white-space: nowrap`** para evitar quebra em linhas estreitas.

### Cards / Containers

- **Corner Style:** Arredondado generoso (10px).
- **Background:** Branco Painel (#ffffff).
- **Shadow:** Card Shadow (ver Elevação).
- **Border:** Sem borda externa. Card-header usa borda inferior (1px solid Borda Fina #e5e7eb) para separar título do conteúdo.
- **Internal Padding:** Card-header: 16px 20px. Card-body: 20px.

### Inputs / Fields

- **Style:** Borda sólida de 1px (Borda Fina #e5e7eb), fundo branco.
- **Shape:** Cantos arredondados (8px).
- **Padding:** 10px 14px. Fonte 0.875rem (inherit).
- **Focus:** Borda muda para Azul Técnico (#3b82f6) com glow sutil (box-shadow 0 0 0 3px rgba(59,130,246,0.1)).
- **Password:** Ícone de toggle de visibilidade à direita (👁️/🙈).

### Navigation (Sidebar)

- **Style:** Painel fixo à esquerda (240px), fundo Azul-Noite Profunda. Altura total da viewport.
- **Header:** Nome do sistema "Gestão TI" (Display) + subtítulo "Painel Administrativo" (Label uppercase, 45% opacidade).
- **Links:** 14px/500, cor rgba(255,255,255,0.7). Ícone (18px) + label.
- **Hover:** Fundo Azul-Noite Hover, cor branca.
- **Active:** Fundo Azul-Noite Ativo, label em Azul Técnico Claro.
- **Mobile (≤700px):** Sidebar colapsa para 60px. Esconde label e header texto, centraliza ícones.

### Tables

- **Style:** Largura total, bordas colapsadas.
- **Header:** Label (12px/600/uppercase/0.04em tracking), cor Texto Secundário, fundo #fafafa, borda inferior Borda Fina.
- **Cells:** Body (13px), borda inferior #f3f4f6. IPs em mono (12px, Texto Secundário).
- **Hover:** Fundo #f9fafb em linhas.
- **Empty/Loading:** Mensagem centralizada com spinner animado.

### Status Indicators

- **Style:** Dot (8px círculo) + texto. Inline-block.
- **Online/Ativo:** Verde (#059669) — dot preenchido + label em verde bold.
- **Offline/Inativo:** Vermelho (#dc2626) — dot preenchido + label em vermelho bold.

### Statistics Cards

- **Style:** Fundo Branco Painel, sombra card, padding 16px 20px, flexível (flex: 1).
- **Number:** 24px/700.
- **Label:** 12px, Texto Secundário.

## 6. Do's and Don'ts

### Do:

- **Do** usar o Azul Técnico exclusivamente para ações e navegação ativa.
- **Do** usar as cores de status (verde/vermelho) apenas para indicar online/offline ou ativo/inativo.
- **Do** manter a sombra de card consistente em todas as superfícies elevadas.
- **Do** dar feedback imediato para toda ação do admin (loading state, mensagem de sucesso/erro).
- **Do** usar a sidebar colapsada em telas ≤700px.

### Don't:

- **Don't** usar o azul de acento como decoração ou em elementos não interativos.
- **Don't** adicionar segundas sombras ou elevações diferentes da padrão.
- **Don't** usar gradientes, glassmorphism, ou texturas decorativas.
- **Don't** misturar estilos de botão entre páginas — todos seguem o mesmo padrão.
- **Don't** remover o indicador de loading durante operações assíncronas.
- **Don't** usar verde/vermelho para funções não relacionadas a status.
- **Don't** aplicar bordas laterais coloridas como acento decorativo em cards.
