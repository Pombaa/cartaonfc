# Cartão de contato — brief pra montar o seu

Referência ao vivo: [andredev21.github.io/andre-portifolio/contacts](https://andredev21.github.io/andre-portifolio/contacts/)

É um cartão digital fullscreen (sem scroll), PT/EN, com retrato ASCII, bio, stack e botões de contato. Copia a pasta `contacts/` pro seu portfólio e troca os dados abaixo.

**Layout atual dos botões (não muda a altura da tela):**
1. Linha de cima — dois botões lado a lado: **WhatsApp ↗** | **LinkedIn ↗**
2. Linha de baixo — botão largo: **Adicionar contato** (baixa um arquivo `.vcf`)
3. Embaixo — links secundários: **GitHub** e **E-mail**

Responde este bloco e devolve. Se não tiver algum item, escreve `não tenho`.

---

## Quem você é

```
Nome completo:
Como quer aparecer no cartão (ex. João P. Silva):
Iniciais (ex. JS):
Cargo em PT (ex. Desenvolvedor Full-Stack · Pleno):
Cargo em EN (ex. Full-Stack Developer · Mid-level):
Cidade / estado / país em PT:
Cidade / estado / país em EN:
Handle curto pra barra do topo (ex. ~/joao):
Nome do arquivo .vcf (ex. joao-silva.vcf):
```

## Bio

Um parágrafo. O do exemplo tem ~400 caracteres — cabe no cartão. Pode mandar só PT que a gente traduz, ou os dois.

```
Bio PT:

Bio EN (opcional):
```

## Stack

Lista o que vai nos chips. 4 a 8 itens funciona bem.

```
Tecnologias (uma por linha):

```

## Links e redes

Cola o URL completo. O cartão padrão tem **WhatsApp** + **LinkedIn** na primeira linha, **Adicionar contato** (`.vcf`) na segunda, e **GitHub** + **e-mail** embaixo. Se tiver outras redes, anota no extra — a gente encaixa.

```
Portfólio (página inicial, pra seta "voltar"):
WhatsApp (número com DDI, ex. 5511999999999):
Mensagem pré-preenchida do WhatsApp (ou deixa o padrão "Olá! Vi seu portfólio."):
LinkedIn:
GitHub:
E-mail:
Telefone pro .vcf (mesmo do WhatsApp, ou outro):

Instagram:
X / Twitter:
Threads:
Discord:
Site / blog:
Calendly / agendamento:
Outro:
```

## Retrato ASCII

O cartão usa a mesma arte ASCII do hero (`ascii-art.js` + `ascii-photo.js` na raiz do site).

```
Quer o retrato ASCII? (sim / não, usa iniciais)
Tem foto de busto com fundo limpo pra gerar a arte? (sim / não)
Se sim, anexa a foto (rosto + ombros, contraste alto, fundo liso).
```

Sem foto, o cartão fica com as iniciais no lugar do retrato — o resto do layout continua igual.

## Visual (opcional)

O exemplo é roxo escuro, cantos retos, vibe Arch/tiling. Se quiser outra cor, manda o hex.

```
Cor de destaque (accent), ou "mantém o roxo":
```

---

## Como encaixa no portfólio

1. Copia a pasta `contacts/` pra `seu-repo/contacts/` (inclui o `index.html` e o `.vcf`).
2. Se for usar o ASCII, copia também `ascii-art.js` e `ascii-photo.js` pra raiz do site (o cartão carrega `../ascii-art.js`).
3. No site principal, o link do cartão é `contacts/` (relativo).
4. Troca no `contacts/index.html`:
   - `~/andre` → teu handle
   - `<h1>` e cargos PT/EN
   - as duas bios (`data-i18n="pt"` / `"en"`)
   - os `<span class="chip">`
   - `href` do WhatsApp (`https://wa.me/55...`), LinkedIn, GitHub e `mailto:`
   - link do botão **Adicionar contato** → teu arquivo `.vcf` (ex. `joao-silva.vcf`)
   - cidade PT/EN
   - `<title>` e meta description
5. Cria o `.vcf` em `contacts/` (vCard 3.0). Modelo mínimo:

```vcf
BEGIN:VCARD
VERSION:3.0
N:Sobrenome;Nome;;
FN:Nome Completo
TITLE:Seu cargo
TEL;TYPE=CELL,VOICE:+5511999999999
EMAIL;TYPE=INTERNET:seu@email.com
URL;TYPE=LinkedIn:https://www.linkedin.com/in/seu-perfil/
URL;TYPE=GitHub:https://github.com/seu-user
ADR;TYPE=HOME:;;Cidade;UF;;País
NOTE:Uma linha curta sobre você.
END:VCARD
```

6. Sobe no GitHub Pages na mesma pasta. URL final: `https://SEU_USER.github.io/SEU_REPO/contacts/`

Arquivos pra editar: `contacts/index.html` + o `.vcf`. Não precisa de build, Node nem framework.

**Dica:** no celular, o `.vcf` costuma abrir direto a tela de salvar contato; no desktop, baixa o arquivo.
