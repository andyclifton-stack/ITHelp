const categories = [
  ["index.html", "Home", "home"],
  ["categories/start-here/index.html", "Start Here", "start-here"],
  ["categories/requests-and-support/index.html", "Requests", "requests-and-support"],
  ["categories/classlink/index.html", "Classlink", "classlink"],
  ["categories/google-workspace/index.html", "Google", "google-workspace"],
  ["categories/microsoft-teams/index.html", "Teams", "microsoft-teams"],
  ["categories/isams/index.html", "iSAMS", "isams"],
  ["categories/printing/index.html", "Printing", "printing"],
  ["categories/office-desk-phones/index.html", "Phones", "office-desk-phones"],
  ["categories/devices-and-windows/index.html", "Devices", "devices-and-windows"],
  ["categories/school-systems/index.html", "Systems", "school-systems"],
  ["categories/files-and-conversion/index.html", "Files", "files-and-conversion"],
  ["categories/room-help/index.html", "Rooms", "room-help"],
  ["categories/security/index.html", "Security", "security"],
];

function normalisePath(path) {
  return path.replace(/\/index\.html$/, "/").replace(/^\//, "");
}

function siteUrl(path) {
  const current = normalisePath(window.location.pathname);
  const repoPrefix = current.startsWith("ITHelp/") ? "/ITHelp/" : "/";
  return `${repoPrefix}${path.replace(/^\//, "")}`;
}

function renderHeader() {
  const currentPath = normalisePath(window.location.pathname);
  const nav = categories
    .map(([href, label]) => {
      const normalisedHref = normalisePath(href);
      const active = currentPath === normalisedHref || currentPath === `ITHelp/${normalisedHref}` ? ' aria-current="page" class="active"' : "";
      return `<a href="${siteUrl(href)}"${active}>${label}</a>`;
    })
    .join("");

  document.getElementById("site-header").innerHTML = `
    <header class="site-header">
      <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav">
        <span></span><span></span><span></span>
        <span class="sr-only">Menu</span>
      </button>
      <nav id="site-nav" class="site-nav" aria-label="Primary navigation">${nav}</nav>
    </header>
  `;
}

function renderFooter() {
  document.getElementById("site-footer").innerHTML = `
    <footer class="site-footer">
      <div class="footer-inner">
        <div class="footer-brand">
          <img src="${siteUrl("assets/img/claremont-logo.png")}" alt="Claremont School">
          <span>Claremont School IT Help</span>
        </div>
        <div class="footer-links">
          <a href="${siteUrl("articles/student-it-help/index.html")}">What if a student needs help?</a>
        </div>
      </div>
    </footer>
  `;
}

function wireNavigation() {
  const button = document.querySelector(".nav-toggle");
  const nav = document.querySelector(".site-nav");
  if (!button || !nav) return;
  button.addEventListener("click", () => {
    const expanded = button.getAttribute("aria-expanded") === "true";
    button.setAttribute("aria-expanded", String(!expanded));
    nav.classList.toggle("open", !expanded);
  });
}

function wireSearch() {
  const input = document.getElementById("site-search");
  const results = document.getElementById("search-results");
  const index = window.IT_HELP_SEARCH_INDEX || [];
  if (!input || !results || !index.length) return;

  const stopWords = new Set(["a", "an", "and", "for", "how", "in", "of", "on", "the", "to", "with", "your"]);

  function normaliseSearchText(value) {
    return String(value || "")
      .toLowerCase()
      .normalize("NFKD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[’']/g, "")
      .replace(/[^a-z0-9]+/g, " ")
      .trim();
  }

  function meaningfulTerms(query) {
    const allTerms = normaliseSearchText(query).split(/\s+/).filter(Boolean);
    const usefulTerms = allTerms.filter((term) => !stopWords.has(term));
    return usefulTerms.length ? usefulTerms : allTerms;
  }

  function words(value) {
    return new Set(normaliseSearchText(value).split(/\s+/).filter(Boolean));
  }

  function render(matches) {
    if (!input.value.trim()) {
      results.innerHTML = "";
      results.classList.remove("active");
      return;
    }
    results.classList.add("active");
    if (!matches.length) {
      results.innerHTML = "<p>No matching guides found.</p>";
      return;
    }
    const visibleMatches = matches.slice(0, 8);
    const status = matches.length > visibleMatches.length
      ? `<p class="search-results-status">Showing ${visibleMatches.length} of ${matches.length} results. Add another word to narrow the list.</p>`
      : `<p class="search-results-status">${matches.length} ${matches.length === 1 ? "result" : "results"}</p>`;
    results.innerHTML = visibleMatches
      .map(
        (item) => `<a href="${siteUrl(item.url)}">
          <strong>${item.title}</strong>
          <span>${item.category} - ${item.summary || "Open guide"}</span>
        </a>`
      )
      .join("") + status;
  }

  input.addEventListener("input", () => {
    const query = normaliseSearchText(input.value);
    const terms = meaningfulTerms(input.value);
    if (!terms.length) {
      render([]);
      return;
    }
    const matches = index
      .map((item) => {
        const title = normaliseSearchText(item.title);
        const category = normaliseSearchText(item.category);
        const summary = normaliseSearchText(item.summary);
        const text = normaliseSearchText(item.text);
        const keywords = normaliseSearchText(item.keywords);
        const titleWords = words(title);
        const categoryWords = words(category);
        const summaryWords = words(summary);
        const textWords = words(text);
        const keywordWords = words(keywords);
        const matchesEveryTerm = terms.every(
          (term) => titleWords.has(term) || categoryWords.has(term) || summaryWords.has(term) || textWords.has(term) || keywordWords.has(term)
        );
        if (!matchesEveryTerm) return { ...item, score: 0 };

        let score = 0;
        if (title === query) score += 1000;
        else if (title.startsWith(query)) score += 700;
        else if (title.includes(query)) score += 500;
        if (keywords.includes(query)) score += 300;
        for (const term of terms) {
          if (titleWords.has(term)) score += 80;
          if (keywordWords.has(term)) score += 40;
          if (categoryWords.has(term)) score += 20;
          if (summaryWords.has(term)) score += 10;
          if (textWords.has(term)) score += 3;
        }
        return { ...item, score };
      })
      .filter((item) => item.score > 0)
      .sort((a, b) => b.score - a.score || a.title.localeCompare(b.title));
    render(matches);
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest(".search-panel")) {
      results.classList.remove("active");
    }
  });

  input.addEventListener("focus", () => {
    if (input.value.trim() && results.innerHTML.trim()) {
      results.classList.add("active");
    }
  });
}

renderHeader();
renderFooter();
wireNavigation();
wireSearch();
