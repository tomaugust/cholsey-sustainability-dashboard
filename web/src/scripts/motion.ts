/** Motion layer (Phase 9, P9.6). Everything it animates is already complete in
 * the server-rendered HTML; this only reveals it. Nothing runs under
 * `prefers-reduced-motion`, and counted numbers always end on the exact
 * server-rendered text. */
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

function countUp(el: HTMLElement) {
  const to = Number(el.dataset.countup);
  const digits = Number(el.dataset.digits ?? 0);
  const final = el.textContent ?? "";
  if (!Number.isFinite(to)) return;
  const fmt = new Intl.NumberFormat("en-GB", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
  const start = performance.now();
  const dur = 1100;
  const tick = (now: number) => {
    const t = Math.min(1, (now - start) / dur);
    const eased = 1 - Math.pow(1 - t, 3);
    el.textContent = t < 1 ? fmt.format(to * eased) : final;
    if (t < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

function reveal(el: Element) {
  el.classList.add("in");
  el.querySelectorAll<HTMLElement>("[data-countup]").forEach(countUp);
  if (el instanceof HTMLElement && el.dataset.countup) countUp(el);
}

const targets = document.querySelectorAll(
  "[data-reveal], .chart, .sparkline-slot, .strip",
);
if (reduced || !("IntersectionObserver" in window)) {
  targets.forEach((el) => el.classList.add("in"));
} else {
  const io = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        // Very tall elements may never reach 20% visible; a fifth of the screen is enough.
        const enough =
          e.intersectionRatio >= 0.2 ||
          e.intersectionRect.height >= innerHeight * 0.2;
        if (!e.isIntersecting || !enough) continue;
        reveal(e.target);
        io.unobserve(e.target);
      }
    },
    { threshold: [0, 0.05, 0.1, 0.2, 0.4] },
  );
  targets.forEach((el) => io.observe(el));
}
