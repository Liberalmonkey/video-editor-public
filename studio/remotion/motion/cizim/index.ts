// cizim ailesi (ADR 0045). Kart M2 el çizimi vurgu bileşenleri.
import type { Tanim } from "../cekirdek/tipler";
import altCizgi from "./alt-cizgi/AltCizgi";
import cagri from "./cagri/Cagri";
import daire from "./daire/Daire";
import fosforlu from "./fosforlu/Fosforlu";
import kutu from "./kutu/Kutu";
import parantez from "./parantez/Parantez";
import ustunuCiz from "./ustunu-ciz/UstunuCiz";

export const CIZIM: Tanim[] = [
  daire,
  altCizgi,
  kutu,
  ustunuCiz,
  fosforlu,
  parantez,
  cagri,
];
