(function () {
  var paletteObserverAttached = false;

  function getMermaidTheme() {
    var scheme =
      (document.body && document.body.getAttribute("data-md-color-scheme")) || "default";
    return scheme === "slate" ? "dark" : "default";
  }

  function captureMermaidSources(root) {
    var scope = root || document;
    scope.querySelectorAll(".mermaid").forEach(function (el) {
      if (el.dataset.mermaidSource) {
        return;
      }
      var text = (el.textContent || "").trim();
      if (text) {
        el.dataset.mermaidSource = text;
      }
    });
  }

  function resetMermaidElements() {
    document.querySelectorAll(".mermaid").forEach(function (el) {
      var src = el.dataset.mermaidSource;
      if (!src) {
        return;
      }
      el.removeAttribute("data-processed");
      el.textContent = src;
    });
  }

  function runMermaid() {
    if (typeof mermaid === "undefined") {
      return;
    }

    captureMermaidSources(document);
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: "loose",
      theme: getMermaidTheme(),
    });
    resetMermaidElements();
    mermaid.run({
      nodes: document.querySelectorAll(".mermaid"),
    });
  }

  document$.subscribe(function () {
    runMermaid();
  });

  function attachPaletteObserver() {
    if (paletteObserverAttached || !document.body) {
      return;
    }
    paletteObserverAttached = true;
    new MutationObserver(function () {
      runMermaid();
    }).observe(document.body, {
      attributes: true,
      attributeFilter: ["data-md-color-scheme"],
    });
  }

  attachPaletteObserver();
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", attachPaletteObserver);
  }
})();
