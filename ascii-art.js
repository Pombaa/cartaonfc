/*
 * ascii-art.js — fit + vinheta no estilo andremmartins.com.br/contacts.
 * Scale uniforme: cabe cabelo→camiseta no room (sem cortar no olho).
 *
 * UMA passada só: onde a foto tem tinta, mostra a tinta (retrato); onde
 * não tem, mostra poeira sintética. Mesma grade, mesmo elemento, mesma
 * escala — não tem como sobrar "costura" entre retrato e fundo porque
 * nunca existiram como duas camadas separadas.
 */
(function () {
  "use strict";

  var BASE = 16;
  /* r < VIG_START fica sempre sólido (sem dithering) — precisa cobrir a
     testa/bochecha, não só o centro exato do rosto. Com 0.50 a testa caia
     bem na faixa de transição (r medido ~0.69, densidade ~68%): invisível
     com 240 colunas (buraco de sub-pixel), virou buraco visível com menos
     colunas (cada célula física maior). */
  var VIG_START = 0.75;
  var VIG_END = 1.35;
  /* Poeira: densidade praticamente CHAPADA (só cai um pouco bem no topo,
     pra combinar com a card-bar) — sem vinheta radial própria. Uma vinheta
     aqui fazia a poeira ficar mais forte perto do rosto e sumir pras
     bordas, lendo como "luz ao redor" (halo), não como fundo contínuo do
     cartão. */
  var DUST_DENSITY = 0.55;
  /* Vários glifos, não só "@" — um glifo repetido lê como bolinhas
     separadas; variar o traço (fino/grosso, várias formas) lê como grão
     contínuo, mesmo na mesma densidade média. */
  var DUST_GLYPHS = ".:-+*#%@=~^";
  /* Deslocamento vertical da elipse da vinheta. A foto atual já começa o
     cabelo na linha 0 (sem sobra de fundo em cima — confirmado inspecionando
     ASCII_PHOTO), então um deslocamento alto (ex.: 1.25) empurra o raio da
     vinheta pra fora bem no topo e apaga o cabelo real, não sobra de fundo
     — é a causa do vão em branco entre a caixa e o cabelo. */
  var VIG_Y_SHIFT = 1.05;

  function isUsablePhoto(value) {
    return typeof value === "string" && value.trim().length > 0;
  }

  function ign(x, y) {
    var v = 0.06711056 * x + 0.00583715 * y;
    v = 52.9829189 * (v - Math.floor(v));
    return v - Math.floor(v);
  }

  function textDims(text) {
    var lines = text.replace(/\n+$/, "").split("\n");
    var cols = 0;
    for (var i = 0; i < lines.length; i++) {
      if (lines[i].length > cols) cols = lines[i].length;
    }
    return { rows: lines.length, cols: cols };
  }

  function dustGlyph(x, y) {
    var idx = Math.floor(ign(x * 7 + 3, y * 11 + 5) * DUST_GLYPHS.length);
    if (idx >= DUST_GLYPHS.length) idx = DUST_GLYPHS.length - 1;
    return DUST_GLYPHS.charAt(idx);
  }

  /* Uma célula por vez: tinta da foto (retrato, some perto da borda) OU
     poeira sintética (preenche o resto, densidade quase uniforme). */
  function compositeArt(text) {
    var lines = text.replace(/\n+$/, "").split("\n");
    var dims = textDims(text);
    var rows = dims.rows;
    var cols = dims.cols;
    if (!rows || !cols) return text;
    var out = [];
    for (var y = 0; y < rows; y++) {
      var line = lines[y] || "";
      while (line.length < cols) line += " ";
      var row = "";
      var topFade = y < rows * 0.04 ? (y / (rows * 0.04)) : 1;
      for (var x = 0; x < cols; x++) {
        var ch = line.charAt(x);
        if (ch !== " ") {
          var nx = (x / (cols - 1 || 1)) * 2 - 1;
          var ny = (y / (rows - 1 || 1)) * 2 - VIG_Y_SHIFT;
          var r = Math.sqrt(nx * nx * 1.15 + ny * ny * 0.85);
          var vig = r < VIG_START
            ? 1
            : Math.max(0, 1 - (r - VIG_START) / (VIG_END - VIG_START));
          vig *= 0.6 + 0.4 * topFade;
          if (vig > 0.06 && ign(x, y) <= vig) {
            row += ch;
            continue;
          }
        }
        /* Sem tinta aqui (ou tinta que não sobreviveu à vinheta): poeira. */
        var dustVig = 0.5 + 0.5 * topFade;
        row += ign(x * 7 + 3, y * 11 + 5) < DUST_DENSITY * dustVig
          ? dustGlyph(x, y)
          : " ";
      }
      out.push(row.replace(/\s+$/, ""));
    }
    return out.join("\n");
  }

  function init() {
    var photo = window.ASCII_PHOTO;
    if (!isUsablePhoto(photo)) return;

    var pre = document.getElementById("portrait-ascii");
    var blur = document.getElementById("portrait-ascii-blur");
    var fallback = document.getElementById("portrait-fallback");
    var portrait = document.getElementById("portrait");
    var rest = document.querySelector(".card-rest");
    var bar = document.querySelector(".card-bar");
    if (!pre || !portrait) return;

    pre.textContent = compositeArt(photo);
    pre.hidden = false;
    /* Camada --blur não existe mais (uma passada só) — garante que fica
       fora do caminho mesmo se o HTML ainda tiver o elemento. */
    if (blur) blur.hidden = true;
    if (fallback) fallback.hidden = true;

    var lastFit = "";
    var measuring = false;

    function applyGeom(scale, left) {
      pre.style.fontSize = BASE + "px";
      pre.style.transform = "scale(" + scale + ")";
      pre.style.left = Math.round(left) + "px";
      pre.style.top = "0px";
    }

    function measureNatural() {
      measuring = true;
      pre.style.fontSize = BASE + "px";
      pre.style.transform = "none";
      var natural = pre.scrollWidth || 1;
      var fullH = pre.scrollHeight || 1;
      measuring = false;
      return { natural: natural, fullH: fullH };
    }

    function fit() {
      if (measuring) return false;
      var target = portrait.clientWidth;
      if (!target) return false;

      var vh = window.innerHeight;
      /* Quando a viewport é mais larga que o cartão (.card trava em
         max-width:420px — desktop, sobra respiro dos LADOS), reserva
         respiro proporcional em cima/embaixo também — senão o cartão
         fica esticado até tocar topo/rodapé da janela enquanto os lados
         já têm margem, layout com cara de bug. Sem isso em mobile: lá a
         viewport IS o cartão (sem sobra lateral), então preencher a
         altura toda é o comportamento certo, não um bug. */
      var isDesktopWidth = window.innerWidth > 460;
      var reserve = isDesktopWidth ? Math.max(24, vh * 0.17) : 24;
      var room = vh
        - reserve
        - (bar ? bar.offsetHeight : 0)
        - (rest ? rest.offsetHeight : 0)
        - 10;
      if (room < 160) room = 160;

      var m = measureNatural();
      /* "Cover" de verdade: a caixa do retrato usa a altura de `room`
         inteira (preenche a tela no mobile; no desktop `room` já tem o
         respiro reservado acima) — e a escala é a MAIOR entre cobrir a
         largura e cobrir essa altura. Cobre os dois eixos sempre; o que
         sobrar (normalmente embaixo, já que a arte é mais alta que larga)
         é cortado pelo overflow:hidden de .portrait/.portrait-slot. Nunca
         reduz pra caber — reduzir tiraria largura da poeira junto (mesma
         grade do retrato agora), abrindo vão nas laterais. */
      var ph = Math.round(room);
      var scale = Math.max(target / m.natural, room / m.fullH);
      var left = (target - m.natural * scale) / 2;

      var key = target + ":" + scale.toFixed(5) + ":" + ph;
      if (key === lastFit) {
        applyGeom(scale, left);
        return true;
      }
      lastFit = key;
      applyGeom(scale, left);
      portrait.style.height = ph + "px";
      return true;
    }

    function tryFit(n) {
      if (fit() || n <= 0) return;
      requestAnimationFrame(function () { tryFit(n - 1); });
    }

    tryFit(12);
    window.addEventListener("resize", fit);
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(fit).catch(function () {});
    }
    if (window.ResizeObserver) {
      new ResizeObserver(function () {
        if (!measuring) fit();
      }).observe(portrait);
      if (rest) {
        new ResizeObserver(function () {
          if (!measuring) fit();
        }).observe(rest);
      }
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
