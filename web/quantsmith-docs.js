/* Optional, same-origin reader for pinned QuantSmith documents. */
(() => {
  const root = document.getElementById("quantsmith-reference");
  if (!root) return;
  const loadButton = document.getElementById("quantsmith-load");
  const search = document.getElementById("quantsmith-search");
  const status = document.getElementById("quantsmith-status");
  const list = document.getElementById("quantsmith-list");
  const source = document.getElementById("quantsmith-source");
  const content = document.getElementById("quantsmith-content");
  const endpoint = "/api/quantsmith/v1/docs";
  let documents = [];
  let revision = "";
  let sourceName = "local checkout";
  let opened = 0;

  async function readJson(path) {
    const response = await fetch(path, { credentials: "same-origin", cache: "no-store" });
    if (!response.ok) throw new Error("The reference is unavailable on this host.");
    return response.json();
  }

  function render() {
    const needle = search.value.trim().toLowerCase();
    const matches = documents.filter((doc) => doc.path.toLowerCase().includes(needle));
    list.replaceChildren();
    for (const doc of matches.slice(0, 100)) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = doc.path;
      button.addEventListener("click", () => openDocument(doc));
      list.append(button);
    }
    status.textContent = `${matches.length} document(s) match. ` +
      (matches.length > 100 ? "Showing the first 100; narrow your search. " : "") +
      `Pinned to ${revision}. Source: ${sourceName}.`;
  }

  async function openDocument(doc) {
    const requested = ++opened;
    content.textContent = "";
    source.textContent = "Loading " + doc.path + "…";
    try {
      const result = await readJson(endpoint + "/" + encodeURIComponent(doc.id));
      if (requested !== opened) return;
      if (result.id !== doc.id || result.commit !== revision) {
        throw new Error("The reference changed; reload its catalog.");
      }
      content.textContent = result.content;
      source.textContent = result.path + " · " + result.commit.slice(0, 12) +
        " · SHA-256 " + result.sha256;
    } catch (error) {
      if (requested === opened) {
        source.textContent = error.message || "The document could not be read.";
      }
    }
  }

  loadButton.addEventListener("click", async () => {
    opened++;
    loadButton.disabled = true;
    status.textContent = "Loading reference catalog…";
    source.textContent = "";
    content.textContent = "";
    try {
      const catalog = await readJson(endpoint);
      if (!Array.isArray(catalog.documents) || typeof catalog.commit !== "string") {
        throw new Error("The reference catalog is invalid.");
      }
      documents = catalog.documents;
      revision = catalog.commit;
      sourceName = catalog.source === "github" ? "GitHub" : "local checkout";
      search.disabled = false;
      render();
    } catch (error) {
      documents = [];
      search.disabled = true;
      list.replaceChildren();
      status.textContent = error.message || "The reference is unavailable.";
    } finally {
      loadButton.disabled = false;
    }
  });
  search.addEventListener("input", render);
})();
