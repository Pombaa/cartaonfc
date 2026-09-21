/*
 * ascii-art.js — renders window.ASCII_PHOTO (set by an optional ascii-photo.js)
 * into the portrait <pre>, fit to its container by width AND height.
 * If ASCII_PHOTO is missing/empty, this script does nothing: the initials
 * fallback already in the HTML stays visible. No console errors either way.
 */
(function () {
  "use strict";

  function isUsablePhoto(value) {
    return typeof value === "string" && value.trim().length > 0;
  }

  function fitAsciiToContainer(pre, container) {
    var PROBE_SIZE = 200; // px, large probe for measurement precision
    pre.style.lineHeight = "1";
    pre.style.fontSize = PROBE_SIZE + "px";

    var naturalWidth = pre.scrollWidth;
    var naturalHeight = pre.scrollHeight;
    if (!naturalWidth || !naturalHeight) return;

    var containerWidth = container.clientWidth;
    var containerHeight = container.clientHeight;
    if (!containerWidth || !containerHeight) return;

    var scale = Math.min(
      containerWidth / naturalWidth,
      containerHeight / naturalHeight
    );
    var fontSize = Math.max(1, PROBE_SIZE * scale);
    pre.style.fontSize = fontSize + "px";
  }

  function init() {
    var photo = window.ASCII_PHOTO;
    if (!isUsablePhoto(photo)) return;

    var pre = document.getElementById("portrait-ascii");
    var fallback = document.getElementById("portrait-fallback");
    var container = document.getElementById("portrait-slot");
    if (!pre || !container) return;

    pre.textContent = photo.replace(/\n+$/, "");
    pre.hidden = false;
    if (fallback) fallback.hidden = true;

    var fit = function () {
      fitAsciiToContainer(pre, container);
    };

    fit();
    window.addEventListener("resize", fit);
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(fit).catch(function () {});
    }
    if (window.ResizeObserver) {
      new ResizeObserver(fit).observe(container);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
