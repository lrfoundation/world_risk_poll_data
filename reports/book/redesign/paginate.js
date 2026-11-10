// Turns each two-column flow into pages, numbers the pages and fills in page references.
// A flow is one tall-enough block of columns: the browser makes more columns to the right
// when the text runs on, and each extra pair of columns becomes a copy of the page, shifted.
(async () => {
  await document.fonts.ready;
  const PITCH = 910; // column width plus gap

  // Number of columns a flow fills, and how far down its last column the text reaches (0 to 1).
  const measure = (flow) => {
    const box = flow.getBoundingClientRect();
    const rects = [];
    for (const el of flow.querySelectorAll("*")) {
      for (const r of el.getClientRects()) if (r.width && r.height) rects.push(r);
    }
    const right = Math.max(0, ...rects.map((r) => r.right));
    const columns = Math.max(1, Math.ceil((right - box.left - 1) / PITCH));
    const edge = box.left + (columns - 1) * PITCH - 1;
    const bottom = Math.max(box.top, ...rects.filter((r) => r.left >= edge).map((r) => r.bottom));
    return { columns, fill: (bottom - box.top) / box.height };
  };

  // A figure with a page of its own must start a page (a left column). Text that follows it is brought
  // forward to fill the page before it, as far as that page has room and up to the next main heading.
  const placePlates = (flow) => {
    const column = (el) => Math.round((el.getBoundingClientRect().left - flow.getBoundingClientRect().left) / PITCH);
    for (const plate of flow.querySelectorAll(".fig.plate")) {
      const fill = plate.nextElementSibling;
      const target = column(plate) + (column(plate) % 2);
      for (;;) {
        // (figures keep their order: the text steps over a column-sized figure that follows the plate)
        let next = fill.nextElementSibling;
        while (next && next.matches(".fig:not(.plate), .roll")) next = next.nextElementSibling;
        if (!next || next.matches("h1, .fig, .platefill")) break;
        const home = next.previousElementSibling;
        plate.before(next);
        if (column(plate) > target) { home.after(next); break; }
      }
      // a heading is not left behind without its text
      while (plate.previousElementSibling && plate.previousElementSibling.matches("h2, h3")) fill.after(plate.previousElementSibling);
      if (column(plate) % 2) {
        const gap = document.createElement("div");
        gap.className = "colbreak";
        plate.before(gap);
      }
    }
  };

  for (const page of [...document.querySelectorAll("section.page.body")]) {
    const flow = page.querySelector(".flow");
    placePlates(flow);
    let { columns, fill } = measure(flow);
    // A few lines alone on a new page or at the top of a column: close up the leading a little to bring them back.
    if ((columns > 2 && columns % 2 === 1 && fill < 0.4) || (columns > 1 && fill < 0.12)) {
      let fitted = false;
      for (const fit of [0.97, 0.94, 0.91, 0.88]) {
        flow.style.setProperty("--fit", fit);
        const tighter = measure(flow).columns;
        if (tighter < columns) { columns = tighter; fitted = true; break; }
      }
      if (!fitted) flow.style.removeProperty("--fit");
    }
    const pages = Math.ceil(columns / 2);
    let last = page;
    for (let k = 1; k < pages; k++) {
      const copy = page.cloneNode(true);
      copy.removeAttribute("id");
      copy.querySelectorAll("[id]").forEach((el) => el.removeAttribute("id"));
      copy.querySelectorAll("[data-ref]").forEach((el) => el.setAttribute("data-copy", ""));
      copy.querySelector(".flow").style.transform = `translateX(${-k * 2 * PITCH}px)`;
      last.after(copy);
      last = copy;
    }
  }

  const roman = (n) => ["", "i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii"][n] || String(n);
  let front = 0, main = 0;
  for (const page of document.querySelectorAll("section.page")) {
    const mode = page.dataset.num;
    const label = mode === "front" ? roman(++front) : mode === "main" ? String(++main) : "";
    page.dataset.label = label;
    const pn = page.querySelector(".pn");
    if (pn) pn.textContent = label;
  }

  const pageOf = (target) => {
    let page = target.closest("section.page");
    const flow = target.closest(".flow");
    if (flow && target !== page) {
      const left = target.getClientRects()[0].left - flow.getBoundingClientRect().left;
      const hops = Math.floor(Math.floor((left + 1) / PITCH) / 2);
      for (let i = 0; i < hops; i++) page = page.nextElementSibling;
    }
    return page.dataset.label;
  };
  const labels = {};
  for (const el of document.querySelectorAll("[data-ref]:not([data-copy])")) {
    const target = document.getElementById(el.dataset.ref);
    labels[el.dataset.ref] = target ? pageOf(target) : "";
  }
  for (const el of document.querySelectorAll("[data-ref]")) el.textContent = labels[el.dataset.ref] || "";
  document.documentElement.dataset.ready = "1";
})();
