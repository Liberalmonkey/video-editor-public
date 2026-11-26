// Arka plan yoklaması: pencere gizliyken istek atmaz, görünür olunca hemen bir kez okur (ADR 0057).
// WHY: Stüdyo arka planda açık kalınca 1,5-4 sn'lik yoklamalar sunucuyu ve CPU'yu boşa meşgul ediyordu.
export const yokla = (fn: () => void, ms: number): (() => void) => {
  const t = window.setInterval(() => { if (!document.hidden) fn(); }, ms);
  const gorunur = () => { if (!document.hidden) fn(); };
  document.addEventListener("visibilitychange", gorunur);
  return () => { window.clearInterval(t); document.removeEventListener("visibilitychange", gorunur); };
};
