(function () {
  "use strict";
  function safeHref(value) {
    try { var url = new URL(String(value || ""), window.location.href); return /^https?:$/.test(url.protocol) ? url.href : "#"; }
    catch (_) { return "#"; }
  }
  // ---- Search modal ---------------------------------------------------
  function initSearchModal() {
    var search = document.querySelector("[data-ps-search]");
    var modal = document.querySelector("[data-ps-search-modal]");
    if (!search || !modal) return;
    var headerInput = search.querySelector(".ps-search__input");
    var headerPrompt = search.querySelector("[data-ps-search-header-prompt]");
    var headerQuery = search.querySelector("[data-ps-search-header-query]");
    var modalForm = modal.querySelector("[data-ps-search-modal-form]");
    var modalInput = modal.querySelector("[data-ps-search-modal-input]");
    var dialog = modal.querySelector(".ps-search-modal__dialog");
    var choices = modal.querySelector(".ps-search-modal__choices");
    var emptyPanel = modal.querySelector("[data-ps-search-empty]");
    var exampleButtons = modal.querySelectorAll("[data-ps-search-example]");
    var docSearch = modal.querySelector("[data-ps-search-docs]");
    var aiSearch = modal.querySelector("[data-ps-search-ai]");
    var aiQueryRow = modal.querySelector("[data-ps-ai-query-row]");
    var aiLoading = modal.querySelector("[data-ps-ai-loading]");
    var challenge = modal.querySelector("[data-turnstile-container]");
    var answer = modal.querySelector("[data-ps-ai-answer]");
    var answerText = modal.querySelector("[data-ps-ai-answer-text]");
    var sources = modal.querySelector("[data-ps-ai-sources]");
    var sourcesList = modal.querySelector("[data-ps-ai-sources-list]");
    var notice = modal.querySelector("[data-ps-ai-notice]");
    var retention = modal.querySelector("[data-ps-ai-retention]");
    var querySlots = modal.querySelectorAll("[data-ps-search-query], [data-ps-ai-query]");
    var suppressNextFocus = false;
    if (!headerInput || !modalForm || !modalInput || !docSearch || !aiSearch) return;

    function query() { return modalInput.value.trim(); }

    function setDialogExpanded(expanded) {
      if (!dialog) return;
      dialog.classList.toggle("ps-search-modal__dialog--expanded", !!expanded);
      dialog.classList.toggle("ps-search-modal__dialog--compact", !expanded);
    }

    function setNotice(kind) {
      if (!notice) return;
      notice.textContent = notice.getAttribute("data-" + kind) || "";
    }

    function setQueryText() {
      var value = query() || modalInput.getAttribute("placeholder") || "";
      querySlots.forEach(function (slot) { slot.textContent = value; });
    }

    function syncHeaderQuery() {
      var value = (headerInput.value || "").trim();
      if (headerQuery) {
        headerQuery.textContent = value;
        headerQuery.hidden = !value;
      }
      if (headerPrompt) headerPrompt.hidden = !!value;
    }

    function setSearchState() {
      var empty = !query();
      if (emptyPanel) emptyPanel.hidden = !empty;
      if (choices) choices.hidden = empty;
      if (empty && notice) notice.textContent = "";
      if (retention) retention.hidden = !empty;
    }

    function escapeHtml(value) {
      return String(value || "").replace(/[&<>"]/g, function (character) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" }[character];
      });
    }

    function renderInlineMarkdown(value) {
      return escapeHtml(value)
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
        .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+|[^\s)]+)\)/g, function (_, label, href) {
          return "<a href=\"" + escapeHtml(safeHref(href)) + "\">" + label + "</a>";
        });
    }

    function renderMarkdown(value) {
      var lines = String(value || "").replace(/\r\n/g, "\n").split("\n");
      var html = [];
      var paragraph = [];
      var listType = null;
      var codeBlock = [];
      var inCode = false;

      function flushParagraph() {
        if (!paragraph.length) return;
        html.push("<p>" + renderInlineMarkdown(paragraph.join(" ")) + "</p>");
        paragraph = [];
      }

      function closeList() {
        if (!listType) return;
        html.push("</" + listType + ">");
        listType = null;
      }

      function openList(type) {
        if (listType === type) return;
        closeList();
        html.push("<" + type + ">");
        listType = type;
      }

      lines.forEach(function (line) {
        var trimmed = line.trim();
        var unordered = trimmed.match(/^[-*]\s+(.+)/);
        var ordered = trimmed.match(/^\d+[.)]\s+(.+)/);

        if (trimmed.indexOf("```") === 0) {
          if (inCode) {
            html.push("<pre><code>" + escapeHtml(codeBlock.join("\n")) + "</code></pre>");
            codeBlock = [];
            inCode = false;
          } else {
            flushParagraph();
            closeList();
            inCode = true;
          }
          return;
        }

        if (inCode) {
          codeBlock.push(line);
          return;
        }

        if (!trimmed) {
          flushParagraph();
          closeList();
          return;
        }

        if (unordered || ordered) {
          flushParagraph();
          openList(unordered ? "ul" : "ol");
          html.push("<li>" + renderInlineMarkdown((unordered || ordered)[1]) + "</li>");
          return;
        }

        closeList();
        paragraph.push(trimmed);
      });

      if (inCode) html.push("<pre><code>" + escapeHtml(codeBlock.join("\n")) + "</code></pre>");
      flushParagraph();
      closeList();
      return html.join("");
    }

    function resetAnswer() {
      if (pendingRequest) { pendingRequest.abort(); pendingRequest = null; }
      resetChallenge();
      if (answer) answer.hidden = true;
      if (answerText) answerText.innerHTML = "";
      if (sources) sources.hidden = true;
      if (sourcesList) sourcesList.innerHTML = "";
      if (retention) retention.hidden = true;
      if (aiLoading) aiLoading.hidden = true;
      if (aiQueryRow) aiQueryRow.hidden = false;
      if (notice) notice.textContent = "";
      setDialogExpanded(false);
    }

    function openModal() {
      if (suppressNextFocus) { suppressNextFocus = false; return; }
      modal.hidden = false;
      modal.setAttribute("aria-hidden", "false");
      document.documentElement.dataset.searchOpen = "true";
      modalInput.value = headerInput.value || "";
      setQueryText();
      resetAnswer();
      setSearchState();
      setTimeout(function () { modalInput.focus(); modalInput.select(); }, 0);
    }

    function closeModal() {
      if (pendingRequest) { pendingRequest.abort(); pendingRequest = null; }
      resetChallenge();
      modal.hidden = true;
      modal.setAttribute("aria-hidden", "true");
      document.documentElement.dataset.searchOpen = "false";
      headerInput.value = modalInput.value;
      syncHeaderQuery();
      suppressNextFocus = true;
      headerInput.focus();
    }

    function searchUrl() {
      var action = modalForm.getAttribute("action") || search.getAttribute("action") || "search.html";
      return new URL(action || window.location.pathname, window.location.href);
    }

    function runDocSearch() {
      var value = query();
      if (!value) { setSearchState(); return; }
      var url = searchUrl();
      url.searchParams.set("q", value);
      url.searchParams.set("check_keywords", "yes");
      url.searchParams.set("area", "default");
      window.location.href = url.toString();
    }

    function apiUrl() {
      var meta = document.querySelector('meta[name="a2rt-ai-endpoint"]');
      return meta ? meta.content : "";
    }

    var pendingRequest = null;
    var turnstileScript = null;
    var turnstileWidget = null;
    function resetChallenge() {
      if (challenge) challenge.hidden = true;
      if (window.turnstile && turnstileWidget !== null) window.turnstile.reset(turnstileWidget);
    }
    function challengeToken(signal) {
      if (!turnstileScript) {
        turnstileScript = new Promise(function (resolve, reject) {
          if (window.turnstile) { resolve(); return; }
          var script = document.createElement("script");
          script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
          script.onload = resolve;
          script.onerror = function () { turnstileScript = null; script.remove(); reject(new Error("Challenge unavailable")); };
          document.head.appendChild(script);
        });
      }
      return turnstileScript.then(function () {
        if (signal.aborted) throw new Error("Aborted");
        if (turnstileWidget !== null) window.turnstile.remove(turnstileWidget);
        return new Promise(function (resolve, reject) {
          var abort = function () { if (turnstileWidget !== null) { window.turnstile.remove(turnstileWidget); turnstileWidget = null; } reject(new Error("Aborted")); };
          signal.addEventListener("abort", abort, { once: true });
          var settle = function (fn, value) { signal.removeEventListener("abort", abort); fn(value); };
          turnstileWidget = window.turnstile.render(challenge, {
            sitekey: document.querySelector('meta[name="a2rt-turnstile-site-key"]').content,
            action: "docs_qa",
            theme: "light",
            callback: function (token) { settle(resolve, token); },
            'error-callback': function () { settle(reject, new Error("Challenge failed")); },
            'expired-callback': function () { settle(reject, new Error("Challenge expired")); }
          });
        });
      });
    }

    function renderSources(items) {
      if (!sources || !sourcesList) return;
      sourcesList.innerHTML = "";
      if (!items || !items.length) {
        sources.hidden = true;
        setNotice("no-sources");
        return false;
      }
      sources.hidden = false;
      var seenTitles = {};
      var renderedCount = 0;
      items.forEach(function (item) {
        if (renderedCount >= 5) return;
        var sourceTitle = String(item.title || item.url || item.docs_url || "").trim();
        var sourceKey = sourceTitle.toLowerCase();
        if (!sourceTitle || seenTitles[sourceKey]) return;
        seenTitles[sourceKey] = true;
        renderedCount += 1;
        var link = document.createElement("a");
        link.className = "ps-search-modal__source";
        link.href = safeHref(item.url || item.docs_url || "#");
        var icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        icon.setAttribute("class", "ps-search-modal__source-icon");
        icon.setAttribute("width", "16");
        icon.setAttribute("height", "16");
        icon.setAttribute("viewBox", "0 0 16 16");
        icon.setAttribute("aria-hidden", "true");
        var path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("fill", "currentColor");
        path.setAttribute("d", "M3.75 1.5A1.75 1.75 0 0 0 2 3.25v9.5c0 .966.784 1.75 1.75 1.75h8.5A1.75 1.75 0 0 0 14 12.75v-7.5a.75.75 0 0 0-.22-.53l-3-3a.75.75 0 0 0-.53-.22h-6.5Zm0 1.5h5.75v2.25c0 .69.56 1.25 1.25 1.25H12.5v6.25a.25.25 0 0 1-.25.25h-8.5a.25.25 0 0 1-.25-.25v-9.5A.25.25 0 0 1 3.75 3Zm7.25.56L11.94 5H11V3.56ZM5 8.25a.75.75 0 0 1 .75-.75h4.5a.75.75 0 0 1 0 1.5h-4.5A.75.75 0 0 1 5 8.25Zm0 2.5a.75.75 0 0 1 .75-.75h4.5a.75.75 0 0 1 0 1.5h-4.5A.75.75 0 0 1 5 10.75Z");
        icon.appendChild(path);
        var body = document.createElement("span");
        body.className = "ps-search-modal__source-body";
        var title = document.createElement("span");
        title.className = "ps-search-modal__source-title";
        title.textContent = sourceTitle;
        body.appendChild(title);
        link.appendChild(icon);
        link.appendChild(body);
        sourcesList.appendChild(link);
      });
      if (!sourcesList.children.length) {
        sources.hidden = true;
        setNotice("no-sources");
        return false;
      }
      return true;
    }

    async function runAiSearch() {
      var value = query();
      if (!value) { setSearchState(); return; }
      if (!apiUrl()) { runDocSearch(); return; }
      if (pendingRequest) pendingRequest.abort();
      var controller = new AbortController();
      pendingRequest = controller;
      var timer = setTimeout(function () { controller.abort(); }, 120000);
      setDialogExpanded(false);
      if (aiQueryRow) aiQueryRow.hidden = true;
      if (aiLoading) aiLoading.hidden = true;
      if (challenge) challenge.hidden = false;
      if (answer) answer.hidden = true;
      if (answerText) answerText.textContent = "";
      if (sources) sources.hidden = true;
      setNotice("verifying");
      try {
        var token = await challengeToken(controller.signal);
        if (controller.signal.aborted) return;
        if (challenge) challenge.hidden = true;
        if (aiLoading) aiLoading.hidden = false;
        setNotice("loading");
        var response = await fetch(apiUrl(), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "omit",
          body: JSON.stringify({
            language: aiSearch.getAttribute("data-ps-language") || "zh",
            question: value,
            currentPath: window.location.pathname,
            turnstileToken: token
          }),
          signal: controller.signal
        });
        if (!response.ok) throw new Error("AI unavailable");
        var payload = await response.json();
        if (pendingRequest !== controller) return;
        setDialogExpanded(true);
        if (answer) answer.hidden = false;
        if (answerText) answerText.innerHTML = renderMarkdown(payload.answer || "");
        if (renderSources(payload.sources || []) && notice) notice.textContent = "";
        if (retention) retention.hidden = false;
      } catch (_) {
        if (pendingRequest === controller && !modal.hidden) { setNotice("error"); if (aiQueryRow) aiQueryRow.hidden = false; }
      } finally {
        clearTimeout(timer);
        if (pendingRequest === controller) {
          // Siteverify tokens are single-use, including failed submissions.
          // Never reset a newer request's widget from an older request.
          resetChallenge();
          pendingRequest = null;
          if (aiLoading) aiLoading.hidden = true;
        }
      }
    }

    search.addEventListener("submit", function (event) { event.preventDefault(); openModal(); });
    search.addEventListener("click", openModal);
    headerInput.addEventListener("focus", openModal);
    headerInput.addEventListener("click", openModal);
    modalInput.addEventListener("input", function () {
      setQueryText();
      resetAnswer();
      setSearchState();
      headerInput.value = modalInput.value;
      syncHeaderQuery();
    });
    exampleButtons.forEach(function (button) {
      button.addEventListener("click", function () {
        modalInput.value = button.getAttribute("data-query") || button.textContent.trim();
        setQueryText();
        resetAnswer();
        setSearchState();
        headerInput.value = modalInput.value;
        syncHeaderQuery();
        runAiSearch();
      });
    });
    modalForm.addEventListener("submit", function (event) { event.preventDefault(); runDocSearch(); });
    docSearch.addEventListener("click", runDocSearch);
    aiSearch.addEventListener("click", runAiSearch);
    modal.querySelectorAll("[data-ps-search-close]").forEach(function (item) {
      item.addEventListener("click", closeModal);
    });
    document.addEventListener("keydown", function (event) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); openModal(); }
      if (!modal.hidden && event.key === "Escape") closeModal();
      if (!modal.hidden && event.key === "Tab") {
        var focusable = Array.from(modal.querySelectorAll('button, input, a[href], [tabindex="0"]')).filter(function (el) { return !el.disabled && el.getClientRects().length; });
        var first = focusable[0], last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
    });
  }

  initSearchModal();
})();
