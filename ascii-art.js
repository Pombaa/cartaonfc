/*
 * ascii-art.js — fit + vinheta no estilo andremmartins.com.br/contacts.
 * Scale uniforme: cabe cabelo→camiseta no room (sem cortar no olho).
 * Vinheta + camada --blur dissolvem a borda.
 */
(function () {
  "use strict";

  /* 1.0 = arte inteira (inclui camiseta); <1 corta embaixo. */
  var SHIRT_CROP = 1.0;
  var BASE = 16;
  var VIG_START = 0.50;
  var VIG_END = 1.10;

  function isUsablePhoto(value) {
    return typeof value === "string" && value.trim().length > 0;
  }

  function ign(x, y) {
    var v = 0.06711056 * x + 0.00583715 * y;
    v = 52.9829189 * (v - Math.floor(v));
    return v - Math.floor(v);
  }

  function vignetteArt(text) {
    var lines = text.replace(/\n+$/, "").split("\n");
    var rows = lines.length;
    var cols = 0;
    var i;
    for (i = 0; i < rows; i++) {
      if (lines[i].length > cols) cols = lines[i].length;
    }
    if (!rows || !cols) return text;
    var out = [];
    for (var y = 0; y < rows; y++) {
      var line = lines[y];
      while (line.length < cols) line += " ";
      var row = "";
      for (var x = 0; x < cols; x++) {
        var ch = line.charAt(x);
        if (ch === " ") {
          row += " ";
          continue;
        }
        var nx = (x / (cols - 1 || 1)) * 2 - 1;
        /* Centro da elipse um pouco abaixo — preserva queixo/camiseta. */
        var ny = (y / (rows - 1 || 1)) * 2 - 1.25;
        var r = Math.sqrt(nx * nx * 1.15 + ny * ny * 0.85);
        var vig = r < VIG_START
          ? 1
          : Math.max(0, 1 - (r - VIG_START) / (VIG_END - VIG_START));
        var topFade = y < rows * 0.04 ? (y / (rows * 0.04)) : 1;
        vig *= 0.6 + 0.4 * topFade;
        if (vig <= 0.06) row += " ";
        else if (ign(x, y) > vig) row += " ";
        else row += ch;
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

    var art = vignetteArt(photo);
    pre.textContent = art;
    pre.hidden = false;
    if (blur) {
      blur.textContent = art;
      blur.hidden = false;
    }
    if (fallback) fallback.hidden = true;

    var lastFit = "";
    var measuring = false;
    var nameBlock = document.querySelector(".name-block");

    function applyGeom(el, scale, left) {
      if (!el) return;
      el.style.fontSize = BASE + "px";
      el.style.transform = "scale(" + scale + ")";
      el.style.left = Math.round(left) + "px";
      el.style.top = "0px";
    }

    function measureNatural() {
      measuring = true;
      pre.style.fontSize = BASE + "px";
      pre.style.transform = "none";
      if (blur) blur.style.transform = "none";
      void pre.offsetWidth;
      var natural = pre.scrollWidth || 1;
      var fullH = pre.scrollHeight || 1;
      measuring = false;
      return { natural: natural, fullH: fullH };
    }

    function fit() {
      if (measuring) return false;
      var target = portrait.clientWidth;
      if (!target) return false;

      var room = window.innerHeight
        - 24
        - (bar ? bar.offsetHeight : 0)
        - (rest ? rest.offsetHeight : 0)
        - 10;
      if (room < 160) room = 160;

      var m = measureNatural();
      var faceH = m.fullH * SHIRT_CROP;
      var scaleW = target / m.natural;
      /* Orçamento de altura: camiseta (~80% da arte) fica acima da zona
         sólida do nome — senão some atrás do name-block. */
      var nameH = nameBlock ? nameBlock.offsetHeight : 110;
      var artBudget = Math.min(room * 0.78, room - nameH * 0.45);
      if (artBudget < 200) artBudget = Math.min(room, 200);
      var scale = Math.min(scaleW, artBudget / faceH);
      var left = (target - m.natural * scale) / 2;
      var ph = Math.round(room);

      var key = target + ":" + scale.toFixed(5) + ":" + ph;
      if (key === lastFit) {
        applyGeom(pre, scale, left);
        applyGeom(blur, scale, left);
        return true;
      }
      lastFit = key;
      applyGeom(pre, scale, left);
      applyGeom(blur, scale, left);
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
