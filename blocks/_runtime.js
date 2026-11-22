// HF blok runtime — tüm bloklar için deterministik yardımcılar.
// WHY: bkz. wiki/concepts/render-sozlesmesi.md — seed'li rastgelelik, Date/Math.random yok,
// her hareket tek paused timeline'da (seek güvenli).
window.HF_BLOCKS = window.HF_BLOCKS || {};
window.HF = (function () {
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function norm(w) {
    return String(w).toLocaleLowerCase("tr").replace(/[^\p{L}\p{N}%]+/gu, "");
  }
  // Metni maskeli kelime span'lerine böl: <span class="w-mask"><span class="w">kelime</span></span>
  function splitWords(el, highlight) {
    const text = (el.textContent || "").trim();
    const hl = new Set(String(highlight || "").split(/\s+/).map(norm).filter(Boolean));
    el.textContent = "";
    const out = [];
    text.split(/\s+/).forEach(function (w, i) {
      const m = document.createElement("span");
      m.className = "w-mask";
      const s = document.createElement("span");
      s.className = "w";
      s.textContent = w;
      if (hl.has(norm(w))) s.classList.add("hl");
      m.appendChild(s);
      el.appendChild(m);
      el.appendChild(document.createTextNode(" "));
      out.push(s);
    });
    return out;
  }
  function maskIn(tl, targets, t, S, o) {
    o = o || {};
    tl.fromTo(targets, { yPercent: 115 }, {
      yPercent: 0, duration: o.dur || S.durations.in, ease: o.ease || S.ease.text,
      stagger: o.stagger === undefined ? S.durations.stagger : o.stagger,
    }, t);
  }
  function fadeUp(tl, el, t, S, o) {
    o = o || {};
    tl.fromTo(el, { opacity: 0, y: o.y === undefined ? 24 : o.y }, {
      opacity: 1, y: 0, duration: o.dur || S.durations.in, ease: o.ease || S.ease.ui,
      stagger: o.stagger || 0,
    }, t);
  }
  function pop(tl, el, t, S, o) {
    o = o || {};
    tl.fromTo(el, { scale: o.from || 0.7, opacity: 0 }, {
      scale: 1, opacity: 1, duration: o.dur || 0.38, ease: S.ease.overshoot, stagger: o.stagger || 0,
    }, t);
  }
  // Blok sonunda kısa çıkış; .clip sarmalayıcıyı runtime gizler, biz içteki .blk'yi soldururuz.
  function exit(tl, el, T, S, o) {
    o = o || {};
    if (o.none) return;
    const d = o.dur || S.durations.out;
    tl.to(el, { opacity: 0, y: o.y === undefined ? -10 : o.y, duration: d, ease: S.ease.exit },
      Math.max(T.start, T.start + T.dur - d));
  }
  // Sayaç: proxy tween + onUpdate (seek güvenli); ondalık ve TR biçimlendirme destekli
  function count(tl, el, t, dur, P, S) {
    const dec = P.decimals || 0;
    const from = Number(P.from || 0), to = Number(P.value || 0);
    const proxy = { v: from };
    const fmt = function (v) {
      return (P.prefix || "") + v.toLocaleString(P.locale || "tr-TR", {
        minimumFractionDigits: dec, maximumFractionDigits: dec }) + (P.suffix || "");
    };
    el.textContent = fmt(from);
    tl.to(proxy, { v: to, duration: dur, ease: S.ease.ui, onUpdate: function () { el.textContent = fmt(proxy.v); } }, t);
  }
  return { mulberry32: mulberry32, norm: norm, splitWords: splitWords, maskIn: maskIn, fadeUp: fadeUp,
    pop: pop, exit: exit, count: count };
})();
