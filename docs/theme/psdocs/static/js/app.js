/* psdocs · app.js — sidebar, drawer, copy-md, toc-highlight */
(function () {
  "use strict";

  // ---- Sidebar tree ----------------------------------------------------
  // Normalize Sphinx's mixed toctree markup so caption categories and regular
  // parent pages use the same collapsible tree-node interaction.
  function initSidebarCollapse() {
    var tree = document.querySelector(".ps-tree");
    if (!tree) return;
    var captions = tree.querySelectorAll(":scope > p.caption, :scope > .caption");
    var chevronSVG =
      '<svg class="ps-chevron" viewBox="0 0 16 16" aria-hidden="true">' +
      '<path fill="currentColor" d="M6.22 3.22a.75.75 0 0 1 1.06 0l4.25 4.25a.75.75 0 0 1 0 1.06l-4.25 4.25a.751.751 0 0 1-1.042-.018.751.751 0 0 1-.018-1.042L9.94 8 6.22 4.28a.75.75 0 0 1 0-1.06Z"/>' +
      "</svg>";

    function directChild(parent, tagName) {
      tagName = tagName.toUpperCase();
      for (var i = 0; i < parent.children.length; i += 1) {
        if (parent.children[i].tagName === tagName) return parent.children[i];
      }
      return null;
    }

    function setExpanded(trigger, list, state) {
      trigger.setAttribute("aria-expanded", state ? "true" : "false");
      list.classList.toggle("ps-collapsed", !state);
    }

    captions.forEach(function (cap) {
      var list = cap.nextElementSibling;
      if (!list || list.tagName !== "UL") return;
      var label = cap.textContent.trim();
      var firstItem = list.firstElementChild;
      if (firstItem && firstItem.tagName === "LI") {
        var firstLink = directChild(firstItem, "a");
        var nested = directChild(firstItem, "ul");
        if (firstLink && nested && firstLink.textContent.trim() === label) {
          var insertBefore = firstItem;
          if (firstLink.classList.contains("current")) {
            cap.classList.add("current");
          }
          while (nested.firstChild) {
            list.insertBefore(nested.firstChild, insertBefore);
          }
          firstItem.remove();
        }
      }
      cap.classList.add("ps-tree-row", "ps-tree-row--category");
      cap.insertAdjacentHTML("beforeend", chevronSVG);
      cap.setAttribute("role", "button");
      cap.setAttribute("tabindex", "0");
      var expanded = true;
      setExpanded(cap, list, expanded);
      function toggle() { setExpanded(cap, list, cap.getAttribute("aria-expanded") !== "true"); }
      cap.addEventListener("click", toggle);
      cap.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); }
      });
    });

    tree.querySelectorAll("li").forEach(function (item) {
      var link = directChild(item, "a");
      var list = directChild(item, "ul");
      if (!link || !list || item.querySelector(":scope > .ps-tree-row")) return;
      var row = document.createElement("div");
      row.className = "ps-tree-row ps-tree-row--page";
      row.insertAdjacentHTML("afterbegin", chevronSVG);
      item.insertBefore(row, link);
      row.appendChild(link);

      var toggle = row.querySelector(".ps-chevron");
      toggle.setAttribute("role", "button");
      toggle.setAttribute("tabindex", "0");
      toggle.setAttribute("aria-label", "展开/收起 " + link.textContent.trim());
      var expanded = link.classList.contains("current") || !!list.querySelector("a.current");
      setExpanded(row, list, expanded);
      function toggleList(e) {
        e.preventDefault();
        e.stopPropagation();
        setExpanded(row, list, row.getAttribute("aria-expanded") !== "true");
      }
      toggle.addEventListener("click", toggleList);
      toggle.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") toggleList(e);
      });
    });
  }

  // ---- Mobile drawer ---------------------------------------------------
  function initDrawer() {
    var toggle = document.querySelector("[data-ps-drawer-toggle]");
    if (!toggle) return;
    var html = document.documentElement;
    toggle.addEventListener("click", function () {
      var open = html.dataset.drawerOpen === "true";
      html.dataset.drawerOpen = open ? "false" : "true";
      toggle.setAttribute("aria-expanded", String(!open));
      html.style.setProperty("--drawer-top", document.querySelector(".docs-toolbar").getBoundingClientRect().bottom + "px");
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && html.dataset.drawerOpen === "true") { html.dataset.drawerOpen = "false"; toggle.setAttribute("aria-expanded", "false"); toggle.focus(); }
    });
    document.addEventListener("click", function (e) {
      if (html.dataset.drawerOpen !== "true") return;
      if (e.target.closest(".ps-sidebar") || e.target.closest("[data-ps-drawer-toggle]")) return;
      html.dataset.drawerOpen = "false";
      toggle.setAttribute("aria-expanded", "false");
    });
  }

  // ---- TOC scroll highlight -------------------------------------------
  function initTocHighlight() {
    var tocLinks = document.querySelectorAll(".ps-toc a[href^='#']");
    if (!tocLinks.length || !("IntersectionObserver" in window)) return;
    var byId = {};
    tocLinks.forEach(function (a) {
      var id = decodeURIComponent(a.getAttribute("href").slice(1));
      byId[id] = a;
    });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var a = byId[e.target.id];
        if (!a) return;
        if (e.isIntersecting) {
          tocLinks.forEach(function (l) { l.removeAttribute("aria-current"); });
          a.setAttribute("aria-current", "true");
        }
      });
    }, { rootMargin: "0px 0px -70% 0px", threshold: 0 });
    Object.keys(byId).forEach(function (id) {
      var el = document.getElementById(id);
      if (el) io.observe(el);
    });
  }

  // Copy the actual Sphinx Markdown source rather than rendered plain text.
  function initCopyMd() {
    var btn = document.querySelector("[data-ps-copy-md-main]");
    if (!btn) return;
    btn.addEventListener("click", async function () {
      try {
        var meta = document.querySelector('meta[name="a2rt-source"]');
        if (!meta) return;
        var response = await fetch(meta.content);
        if (!response.ok) throw new Error("Source unavailable");
        await navigator.clipboard.writeText(await response.text());
        showCopiedToast();
      } catch (_) {
        var original = btn.title;
        btn.title = document.documentElement.lang.startsWith("zh") ? "无法复制，请手动选择内容" : "Copy unavailable; select the text manually";
        btn.setAttribute("aria-label", btn.title);
        setTimeout(function () { btn.title = original; btn.removeAttribute("aria-label"); }, 2500);
      }
    });
  }

  function showCopiedToast() {
    var t = document.createElement("div");
    t.textContent = "Copied!";
    t.style.cssText = [
      "position:fixed", "left:50%", "bottom:32px",
      "transform:translateX(-50%)",
      "padding:8px 16px",
      "background:rgba(31,35,40,0.9)", "color:#fff",
      "border-radius:6px", "font-size:14px",
      "z-index:2000", "box-shadow:0 8px 24px rgba(0,0,0,0.2)"
    ].join(";");
    document.body.appendChild(t);
    setTimeout(function () { t.remove(); }, 1800);
  }

  function init() {
    initSidebarCollapse();
    initDrawer();
    initTocHighlight();
    initCopyMd();
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
