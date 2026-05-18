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
    results.innerHTML = matches
      .slice(0, 8)
      .map(
        (item) => `<a href="${siteUrl(item.url)}">
          <strong>${item.title}</strong>
          <span>${item.category} - ${item.summary || "Open guide"}</span>
        </a>`
      )
      .join("");
  }

  input.addEventListener("input", () => {
    const terms = input.value
      .toLowerCase()
      .split(/\s+/)
      .filter(Boolean);
    if (!terms.length) {
      render([]);
      return;
    }
    const matches = index
      .map((item) => {
        const haystack = `${item.title} ${item.category} ${item.summary} ${item.text}`.toLowerCase();
        const score = terms.reduce((total, term) => total + (haystack.includes(term) ? 1 : 0), 0);
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
