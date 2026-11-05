(() => {
  const app = document.getElementById("app");
  const q = document.getElementById("q");
  const PAGE = 50;
  let docs = null;

  const el = (tag, props = {}, ...kids) => {
    const e = Object.assign(document.createElement(tag), props);
    e.append(...kids);
    return e;
  };

  async function loadIndex() {
    if (!docs) {
      const r = await fetch("index.json");
      if (!r.ok) throw new Error("Kunde inte läsa index.json");
      docs = await r.json();
    }
    return docs;
  }

  const norm = (s) => s.toLowerCase().replace(/[\s:]+/g, " ").trim();

  async function renderList(query, page) {
    app.replaceChildren(el("p", { textContent: "Laddar…" }));
    const all = await loadIndex();
    const terms = norm(query).split(" ").filter(Boolean);
    const hits = terms.length
      ? all.filter((d) => {
          const hay = norm(d.t + " " + d.n);
          return terms.every((t) => hay.includes(t));
        })
      : all;
    const pages = Math.max(1, Math.ceil(hits.length / PAGE));
    page = Math.min(Math.max(1, page), pages);
    const ul = el("ul", { className: "list" });
    for (const d of hits.slice((page - 1) * PAGE, page * PAGE)) {
      ul.append(el("li", {},
        el("a", { href: "#/lag/" + encodeURIComponent(d.id), textContent: d.t }),
        el("small", { textContent: [d.n, d.y, d.d].filter(Boolean).join(" · ") })));
    }
    const link = (label, p) => el("a", {
      href: "#/?q=" + encodeURIComponent(query) + "&p=" + p, textContent: label });
    const pager = el("div", { className: "pager" },
      page > 1 ? link("← Föregående", page - 1) : "",
      el("span", { textContent: `${hits.length} träffar · sida ${page}/${pages}` }),
      page < pages ? link("Nästa →", page + 1) : "");
    app.replaceChildren(pager, ul);
  }

  // Minimal, XSS-safe renderer: only headings, bold, rules and paragraphs; all text via textContent.
  function inline(parent, text) {
    text.split(/(\*\*[^*]+\*\*)/).forEach((part) => {
      if (/^\*\*[^*]+\*\*$/.test(part)) parent.append(el("strong", { textContent: part.slice(2, -2) }));
      else if (part) parent.append(part);
    });
  }

  function renderMarkdown(md) {
    const box = el("article", { className: "law" });
    for (const block of md.split(/\n{2,}/)) {
      const b = block.replace(/\s+$/, "");
      if (!b.trim()) continue;
      if (/^---+$/.test(b.trim())) { box.append(el("hr")); continue; }
      const h = b.match(/^(#{1,6})\s+([\s\S]*)$/);
      if (h) {
        const n = Math.min(h[1].length + 0, 6);
        const hd = el("h" + n);
        inline(hd, h[2].replace(/\n/g, " "));
        box.append(hd);
        continue;
      }
      const p = el("p");
      inline(p, b);
      box.append(p);
    }
    return box;
  }

  async function renderLaw(id) {
    app.replaceChildren(el("p", { textContent: "Laddar…" }));
    if (!/^[\w.-]+$/.test(id)) { app.replaceChildren(el("p", { textContent: "Ogiltigt id." })); return; }
    const r = await fetch("md/" + id + ".md");
    if (!r.ok) { app.replaceChildren(el("p", { textContent: "Författningen hittades inte." })); return; }
    const md = await r.text();
    const t = md.match(/^#\s+(.+)$/m);
    if (t) document.title = t[1] + " – Legalize SE";
    app.replaceChildren(
      el("p", {}, el("a", { href: "#/", textContent: "← Alla författningar" })),
      renderMarkdown(md));
    window.scrollTo(0, 0);
  }

  async function route() {
    document.title = "Legalize SE – Svensk författningssamling";
    const hash = location.hash.replace(/^#/, "") || "/";
    const [path, qs = ""] = hash.split("?");
    const params = new URLSearchParams(qs);
    try {
      if (path.startsWith("/lag/")) {
        await renderLaw(decodeURIComponent(path.slice(5)));
      } else {
        q.value = params.get("q") || "";
        await renderList(q.value, parseInt(params.get("p") || "1", 10) || 1);
      }
    } catch (e) {
      app.replaceChildren(el("p", { textContent: String(e.message || e) }));
    }
  }

  let timer;
  q.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      location.hash = "#/?q=" + encodeURIComponent(q.value);
    }, 200);
  });
  window.addEventListener("hashchange", route);
  route();
})();
