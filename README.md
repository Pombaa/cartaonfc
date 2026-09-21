# Cartão de contato — João V. Ferreira

Cartão de contato digital fullscreen (sem scroll), bilíngue PT/EN, 100% estático.
O que vai pro GitHub Pages não muda de natureza: HTML + CSS + JS vanilla
inline e um `.vcf`, sem build, sem Node, sem framework, sem dependência
externa em runtime.

Tudo o que você normalmente editaria à mão mora em **`card.config.json`**.
Um script de dev (`tools/sync.py`) lê esse arquivo e regenera o HTML e o
`.vcf`. Você não edita `contacts/index.html` nem o `.vcf` diretamente.

```
cartao/
  card.config.json           fonte única de verdade: nome, bio, links, cor, etc.
  ascii-art.js                renderer do retrato ASCII (raiz do site) — deploy
  contacts/
    index.html                 a página do cartão — deploy
    joao-ferreira.vcf           vCard 3.0 gerado a partir do config — deploy
    og.png                      (opcional) gerado por `sync.py --og` — deploy
  ascii-photo.js              (opcional) gerado quando "photo" existe — deploy
  requirements-dev.txt        deps de dev pinadas — NÃO faz parte do deploy
  tools/                      só dev, NÃO faz parte do deploy
    sync.py                     comando principal: config -> HTML + .vcf + ascii
    verify.py                   roda a bateria de testes em cópias temporárias
    gen-ascii.py                gera ascii-photo.js a partir de uma foto (avulso)
    _cardlib.py, _vcf.py,       módulos internos compartilhados por sync.py/
    _html_regions.py, _ascii_core.py   verify.py/gen-ascii.py
```

**O que publicar no GitHub Pages:** `ascii-art.js`, `contacts/` (inclui o
`.vcf` e, se você gerou, `og.png`), `ascii-photo.js` se você tiver uma
foto, e `.nojekyll` (raiz — evita que o Pages tente processar o site como
Jekyll, o que ignoraria arquivos/pastas começando com `_`). **Não publique
`tools/`, `card.config.json` nem `assets/`** (a foto de origem) — nada ali
é necessário em produção, e `card.config.json` não tem dado sensível mas
também não precisa estar público.

## Rotina do dia a dia

```bash
# 1. edite card.config.json (nome, bio, links, accent, etc.)
# 2. rode:
python3 tools/sync.py
# 3. confira: python3 -m http.server 8000, abra http://localhost:8000/contacts/
```

`tools/sync.py` regenera `contacts/index.html` (só as partes marcadas com
`sync:start:*`/`sync:end:*`, o resto do arquivo é seu para editar
livremente), o `.vcf`, e `ascii-photo.js` se `"photo"` estiver definido. É
idempotente: rodar duas vezes seguidas sem mudar o config não altera nada.

Dependências de dev (versões pinadas em `requirements-dev.txt`; nenhuma vai
para o site publicado):

```bash
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python3 -m playwright install chromium
```

`Pillow` é sempre necessário (ascii-art a partir de foto). `vobject` é
opcional (valida o `.vcf` gerado por `sync.py`/`verify.py`; sem ele, os dois
só avisam que pularam a validação). `playwright` é necessário só para
`sync.py --og` e `verify.py`.

## Pendências

Rode `python3 tools/sync.py --check` a qualquer momento — ele lista o que
falta preencher, o efeito de cada pendência e o comando exato para resolver.
Resumo (3 linhas cada):

- **Foto** → solte o arquivo em `assets/foto.jpg` (ou outro caminho), defina
  `"photo"` em `card.config.json`, rode `python3 tools/sync.py`.
- **Link do portfólio** (seta de voltar) → preencha `"portfolio_url"`, rode
  `python3 tools/sync.py`.
- **URL do site (GitHub Pages)** → preencha `"site_url"` (ex.
  `"https://pombaa.github.io/meu-repo"`), rode `python3 tools/sync.py`.
- **Imagem de compartilhamento** → rode `python3 tools/sync.py --og`
  (screenshota o próprio cartão e já preenche `"og_image"`).
- **Redes extras** (Instagram, X, Discord, etc.) → adicione até 4 itens em
  `"extras"` (`{"label": "...", "url": "..."}`), rode `python3 tools/sync.py`.

## `card.config.json` — campos

| Campo | Efeito |
|---|---|
| `name`, `display_name`, `initials` | nome completo (usado no `.vcf`), nome exibido (`<h1>`, `<title>`, aria-labels), iniciais do fallback |
| `handle` | texto da barra superior (`~/pomba`) |
| `role.pt/en`, `location.pt/en`, `bio.pt/en` | textos bilíngues (cargo, localização, bio) |
| `chips` | lista de tecnologias (ordem preservada) |
| `wa_number`, `wa_message` | WhatsApp: número com DDI (só dígitos) e mensagem pré-preenchida |
| `linkedin`, `github`, `email`, `phone` | links diretos e dados do `.vcf` |
| `vcf_filename` | nome do arquivo `.vcf` (troque em `href`/`download` automaticamente) |
| `vcf_note` | se preenchido, vira o campo `NOTE` do `.vcf` literalmente; se `null`, mantém a derivação automática (`role.pt` + `chips`) |
| `accent` | cor de destaque (hex). `accent_soft` é opcional — se `null`, é derivada automaticamente de `accent` |
| `portfolio_url` | se preenchido, ativa a seta "← voltar" na barra superior |
| `site_url` | base do GitHub Pages (ex. `"https://pombaa.github.io/cartaonfc"`, sem `/contacts`); ativa `og:url` e `<link rel="canonical">` |
| `og_image` | nome do arquivo (ex. `"og.png"`) ou URL completa; ativa `og:image`/`twitter:card` |
| `meta_description` | texto do `<meta name="description">`; se `null`, deriva de `chips` (mesma fórmula do `og:description`) |
| `labels.whatsapp`, `labels.linkedin`, `labels.github` | texto dos botões/links WhatsApp, LinkedIn e GitHub (mesmo texto em PT/EN — nomes próprios) |
| `labels.add_contact.pt/en`, `labels.email.pt/en` | texto bilíngue do botão "Adicionar contato"/"Add contact" e do link "E-mail"/"Email" |
| `photo` | caminho da foto de origem, relativo à raiz do repo; `null` = fallback de iniciais |
| `ascii.cols` | colunas do ASCII (padrão 100) |
| `ascii.contrast` | fator de contraste extra, 1.0 = sem alteração |
| `ascii.gamma` | correção de gama, 1.0 = sem alteração |
| `ascii.invert` | inverte o mapeamento claro/escuro → densidade (caso raro) |
| `ascii.crop` | `{"x","y","w","h"}` em frações 0–1, ou `null` para recorte automático central (~3:4) |
| `extras` | até 4 `{"label", "url"}` — aparecem junto de GitHub/E-mail. `url` pode ser `mailto:`/`tel:` |

Um campo com `null` (ou lista vazia) nunca é renderizado — o layout se
reajusta sem buraco.

Se seu nome não separar corretamente em nome/sobrenome no `.vcf` (a
heurística assume o padrão "conector como de/da/dos" do português), defina
`name_given` e `name_family` no config para sobrescrever.

## Comandos

- `python3 tools/sync.py` — aplica o config a `contacts/index.html` e ao
  `.vcf`, gera/remove `ascii-photo.js`.
- `python3 tools/sync.py --check` — lista pendências (sempre sai com código 0).
- `python3 tools/sync.py --og` — gera `contacts/og.png` (1200×630) via
  screenshot do próprio cartão + fundo do tema, e preenche `og_image`.
- `python3 tools/verify.py` — roda a bateria de aceite (zero scroll, zero
  request externo, zero erro de console, hrefs, contraste AA, `.vcf`
  válido, teclado, i18n) em 12 viewports × PT/EN, em 4 cenários (incluindo
  `subpath`, sob `/cartaonfc/`), cada um numa cópia temporária do projeto
  (nunca suja este repositório).
- `python3 tools/gen-ascii.py foto.jpg [--columns N] [--contrast] [--gamma]
  [--invert] [--crop x,y,w,h] [--output caminho]` — gera um `ascii-photo.js`
  avulso, sem tocar no config. Para o fluxo normal, prefira definir `"photo"`
  no config e rodar `sync.py`.

## Retrato ASCII

Sem foto, o cartão mostra as iniciais num quadro tracejado (mesmo espaço que
o retrato ASCII ocuparia — ambos preenchem o mesmo "slot" de proporção 3:4).
Com `"photo"` definido, `tools/sync.py`:

1. Lê a foto (jpg/png/webp), corrige orientação EXIF.
2. Recorta para ~3:4 (automático e central, ou manual via `ascii.crop`).
3. Normaliza contraste (`autocontrast`) e aplica `ascii.contrast`/`ascii.gamma`.
4. Redimensiona para `ascii.cols` colunas, corrigindo a proporção do
   caractere de fonte monoespaçada (~2:1 altura/largura).
5. Mapeia luminância para a rampa `" .:-=+*#%@"` — como o tema é escuro
   (texto claro sobre fundo escuro), o mapeamento é invertido em relação ao
   ASCII-art clássico: pixel **claro** vira caractere **denso** (mais "tinta"
   colorida visível), pixel escuro vira espaço (fundo aparece). `ascii.invert`
   inverte de volta, caso necessário.
6. Avisa (sem travar) se a foto tiver baixo contraste ou fundo pouco uniforme.

`ascii-art.js` (no navegador) só faz o "fit": se `window.ASCII_PHOTO` existe,
mostra o `<pre>` e ajusta o `font-size` para caber no slot (largura e
altura); senão, não faz nada e o fallback de iniciais (já no HTML) continua
visível — sem erro em nenhum dos dois caminhos.

## Publicar no GitHub Pages

O repositório (`git@github.com:Pombaa/cartaonfc.git`, branch `master`) já
existe. `site_url` em `card.config.json` já está preenchido com
`https://pombaa.github.io/cartaonfc`.

1. Rode `python3 tools/sync.py` (e `--og` se quiser imagem de compartilhamento).
2. Comite e faça push de `ascii-art.js`, `contacts/` (com o `.vcf` e `og.png`
   se houver), `ascii-photo.js` (se houver foto) e `.nojekyll` para `master`.
   **Não suba** `tools/`, `card.config.json` nem `assets/` (a foto de
   origem) — veja `.gitignore`.
3. No GitHub: **Settings → Pages → Deploy from a branch** → branch `master`,
   pasta `/ (root)`.
4. URL final: `https://pombaa.github.io/cartaonfc/contacts/`.

## Visual

Tema escuro, cantos retos (`border-radius: 0`), fonte monoespaçada com stack
de fallback do sistema (`ui-monospace`, `JetBrains Mono`, `Cascadia Mono`,
`Segoe UI Mono`, `SFMono-Regular`, `Menlo`, `Consolas`, `Liberation Mono`,
`monospace` — sem webfont externa, zero requests de rede). Cor de destaque
padrão `#a875ff` (roxo/lavanda), verificada com contraste AA sobre o fundo
`#0b0710` (razão ≈ 6.3:1, acima do mínimo 4.5:1). Troque em `accent` no
config; `accent_soft` (fundo do botão outline do WhatsApp) é derivada
automaticamente se você não fixar um valor.

## Decisões e desvios

- **Marcadores no HTML**: `contacts/index.html` tem comentários
  `sync:start:<nome>`/`sync:end:<nome>` (HTML ou CSS) delimitando o que
  `sync.py` reescreve. Fora deles, o arquivo é seu — estrutura, CSS de
  layout e o script de i18n/ASCII (genérico, lê `data-i18n`/`data-aria-*`,
  não tem texto hardcoded) podem ser editados livremente.
- **Labels de botões/links agora em `card.config.json`**: "WhatsApp",
  "LinkedIn", "GitHub" e o par bilíngue "Adicionar contato"/"Add contact",
  "E-mail"/"Email" viraram `labels.*` no config (ver tabela acima) — antes
  eram string Python fixa em `_html_regions.py`. Valores padrão idênticos
  ao texto anterior, então o HTML gerado não muda até você editar o campo.
  **Não editável via config** (texto realmente estático, não é dado do
  usuário): os rótulos "PT"/"EN" do toggle de idioma e o
  `aria-label="Idioma / Language"` do grupo — são identificadores de
  idioma amarrados ao JS (`#btn-pt`/`#btn-en`), não copy de interface.
- **Meta description agora em `card.config.json`** (`meta_description`):
  antes ficava fora dos marcadores, só editável à mão no HTML. Se `null`,
  deriva de `chips` com a mesma fórmula do `og:description`; o config já
  vem com o texto editorial anterior, então o `<meta>` gerado é
  byte-idêntico ao de antes.
- **NOTE do `.vcf`**: antes era um resumo curado à mão (omitia MySQL,
  reagrupava "Linux/Docker"); agora é derivado automaticamente de
  `role.pt` + `chips` (lista completa) — texto ligeiramente diferente, dado
  idêntico e mais completo, e agora nunca fica desatualizado.
- **Nome/sobrenome do `.vcf`**: heurística por conectores (de/da/dos/das) —
  ver "campo `name_given`/`name_family`" acima para casos que ela erre.
- **`accent_soft`**: se não fixado no config, é derivado misturando
  `accent` com o fundo do tema — muda ligeiramente o tom se você só trocar
  `accent`, mas mantém o esquema coerente sem exigir um segundo campo manual.
- **Aria-labels do retrato**: agora usam `display_name` de forma consistente
  (antes usavam o nome completo "João Vitor Ferreira" nesse texto específico)
  — mudança invisível (não é texto renderizado), feita para eliminar a
  duplicação de string hardcoded no JS.
- **Bloco do retrato**: `flex: 0 1 clamp(72px, 20vh, 190px)` — mesmo
  tamanho "normal" de antes (não muda no caso comum), mas agora pode
  encolher (nunca abaixo de `clamp(56px, 15vh, 90px)`) quando conteúdo
  extra (ex. 4 redes extras) precisaria de mais espaço do que a viewport
  tem. Isso corrigiu um recorte (não pego pelo teste de scroll de página,
  só visível medindo as caixas): com o retrato de tamanho fixo antigo,
  4 extras em 360×640 estouravam a altura do cartão e os dois últimos links
  ficavam cortados por `overflow: hidden`, sem gerar scroll na página (por
  isso passou despercebido antes). A régua de contenção (ver
  `tools/verify.py`, checagem `CLIPPED`) agora testa isso diretamente.
- **360×640, caso sem extras**: o mesmo ajuste também encolhe o retrato em
  ~5px nesse único viewport (de 128px para ~123px) porque o conteúdo total
  já encostava no limite da tela por essa margem — antes esse excesso
  provavelmente era cortado silenciosamente pelo `overflow:hidden` do
  cartão (idem acima); agora é absorvido de forma controlada pelo retrato.
  Comparado nos outros 8 pares viewport×idioma, a tela é pixel-idêntica à
  versão anterior.
- **Ícone dos links "extras"**: usa a mesma seta genérica dos botões
  WhatsApp/LinkedIn (não há um ícone dedicado por rede social).
- **`vcf_note`** (novo campo, `null` por padrão): se preenchido, substitui
  o `NOTE` do `.vcf` pelo texto exato; com `null`, mantém a derivação
  automática (`role.pt` + `chips`) — nenhuma mudança no `.vcf` atual.
- **`site_url` preenchido** (`https://pombaa.github.io/cartaonfc`): ativa
  `og:url`/`<link rel="canonical">` apontando para
  `https://pombaa.github.io/cartaonfc/contacts/`. `og_image` continua
  `null` (depende de foto), então nenhuma tag `og:image` é emitida ainda.
- **Paths relativos para GitHub Pages de project site**: todo `href`/`src`
  em `contacts/index.html` já era relativo (`joao-ferreira.vcf`,
  `../ascii-art.js`) — nenhuma mudança foi necessária. `tools/verify.py`
  agora prova isso com um cenário `subpath`, que serve o projeto sob
  `/cartaonfc/` (handler de `http.server` que remove o prefixo antes de
  resolver o arquivo) e roda a mesma bateria de aceite nele.
- **Compactação em baixa altura** (`@media (max-height: 620px)`): tipografia
  e gaps encolhem (o retrato já encolhe sozinho pelo `clamp()` em
  `.portrait`, sem precisar de regra extra). O layout dos botões (linha
  WhatsApp|LinkedIn, botão largo "Adicionar contato", linha de links
  secundários) não muda, só os tamanhos. Nenhum viewport ≥640px de altura
  (os 5 já aprovados) é afetado — o breakpoint fica abaixo do menor deles.
- **Retrato só é ocultado quando encolher não basta** (revisão da regra
  acima): medi por bisseção com Playwright (largura fixa, altura variando,
  script ad-hoc, não versionado) até onde o encolhimento natural do
  retrato (`min-height: clamp(56px, 15vh, 90px)`) mais a compactação acima
  dão conta sozinhos, sem esconder nada:
  - **Paisagem**: o `.card` trava em `max-width: 440px`, então largura
    extra não ajuda o layout vertical — o piso medido é ~398px em
    qualquer largura ≥440px (testado 640–1920px), igual em todos os
    cenários. `@media (orientation: landscape) and (max-height: 500px)`
    esconde o retrato só abaixo disso (640×360 e 844×390 continuam
    escondendo; 1024×600 agora **mostra** o retrato encolhido).
  - **Retrato (celular em pé)**: piso medido 373–416px conforme largura
    (360–393px, testado com conteúdo atual e com o retrato ASCII de
    teste — idêntico nos dois, o encolhimento não depende do tipo de
    retrato) e cenário (pior caso: `portfolio-site-extras`, 4 extras +
    seta de voltar, em inglês, 375px de largura). `@media (orientation:
    portrait) and (max-height: 440px)` cobre o pior caso com folga — os 4
    viewports novos de celular com barra (548–700px de altura) ficam bem
    acima e mostram o retrato normalmente.
- **Viewports "celular com barra de navegador"** (375×548, 360×560,
  390×664, 393×700): a barra de endereço/navegação do Chrome/Safari mobile
  reduz a altura *útil* do viewport bem abaixo da altura "cheia" do
  device — testam exatamente a faixa onde o retrato encolhe mas não
  chega a sumir.
- **`requirements-dev.txt`**: versões pinadas (Pillow, playwright,
  vobject) para reprodutibilidade — nenhuma delas é usada em runtime pelo
  site publicado.
- **Fallback de `dvh`**: `body` declara `height: 100vh` antes de
  `height: 100dvh` — navegadores sem suporte a `dvh` simplesmente ignoram a
  segunda declaração e ficam com `vh`; navegadores com suporte usam a
  última declaração válida (`dvh`), como já era.

## Verificação

`python3 tools/verify.py` roda, para cada um de 4 cenários — (i) estado
atual do config, (ii) com foto sintética, (iii) com `portfolio_url` +
`site_url` + 4 extras, (iv) **subpath**: serve o projeto sob `/cartaonfc/`
(um handler mínimo de `http.server` remove o prefixo antes de resolver o
arquivo), replicando como o GitHub Pages de *project site* monta a URL —,
em 12 viewports × PT/EN:

- 360×640, 390×844, 768×1024, 1366×768, 1920×1080 (retrato/paisagem normais).
- 640×360, 844×390, 1024×600 (celular deitado / janela baixa — retrato
  encolhe e, abaixo de 500px de altura em paisagem, some).
- 375×548, 360×560, 390×664, 393×700 (celular em pé com barra de
  navegador — faixa onde o retrato encolhe mas não chega a sumir; some só
  abaixo de 440px de altura em pé).

Critérios, iguais em todos os cenários/viewports:

- Zero scroll de página **e** zero elemento (chip/botão/link) com a caixa
  fora dos limites do cartão (recorte silencioso por `overflow: hidden`).
- Zero requests externos, zero erro/warning de console.
- Todos os `href` por valor exato (WhatsApp com número+texto codificados,
  LinkedIn, GitHub, `mailto:`, `.vcf` com o nome certo, baixado de verdade).
- `.vcf` parseado com `vobject`, CRLF, dobra de linha ≤75 octetos.
- Toggle PT/EN, `?lang=`, ordem de tab, `:focus-visible`.
- Contraste calculado (não estimado) para todo texto/botão relevante.

Cada cenário roda numa cópia temporária do projeto (`tempfile.mkdtemp`), que
é apagada ao final — o repositório nunca é alterado por `verify.py`. Como
evidência visual (não como critério de pass/fail), os 7 viewports
baixos/com-barra são fotografados em
`verify-output/<cenário>/<viewport>_<lang>.png` (git-ignorado, sobrescrito
a cada execução).
