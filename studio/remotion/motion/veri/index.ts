// veri ailesi (ADR 0045). Aile kartı bileşenlerini buraya ekler.
import type { Tanim } from "../cekirdek/tipler";
import adimlar from "./adimlar/Adimlar";
import cizgi from "./cizgi/Cizgi";
import cubuk from "./cubuk/Cubuk";
import halka from "./halka/Halka";
import karsilastirma from "./karsilastirma/Karsilastirma";
import odometre from "./odometre/Odometre";
import sayac from "./sayac/Sayac";

export const VERI: Tanim[] = [
  sayac,
  odometre,
  cubuk,
  cizgi,
  halka,
  karsilastirma,
  adimlar,
];
