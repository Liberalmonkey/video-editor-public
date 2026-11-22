// React adasında SplitReel'in yerel font yükleyicisinin yerine (paketle.ts yönlendirir).
// WHY: bkz. wiki/decisions/0051-uctan-uca-hyperframes.md. Yükleyici paketin göreli font adresini belgeye göre çözüyordu
// (önizlemede /pub/.../Montserrat-Variable.ttf, 404). HyperFrames kompozisyonunda fontlar tema.css @font-face'tedir; aileler
// aynı adla döner.
export const loadCaptionFont = () => ({ fontFamily: "Montserrat" });
export const loadSpaceGrotesk = (_w: string[]) => ({ fontFamily: "Space Grotesk" });
export const loadPlayfair = (_s: "normal" | "italic", _w: string[]) => ({ fontFamily: "Playfair Display" });
