// zemin ailesi (ADR 0045). Aile kartı bileşenlerini buraya ekler.
import type { Tanim } from "../cekirdek/tipler";
import grenliGradyan from "./grenli-gradyan/GrenliGradyan";
import grid from "./grid/Grid";
import halftone from "./halftone/Halftone";
import kagit from "./kagit/Kagit";
import noktaIzgara from "./nokta-izgara/NoktaIzgara";

export const ZEMIN: Tanim[] = [
  grid,
  noktaIzgara,
  grenliGradyan,
  kagit,
  halftone,
];
