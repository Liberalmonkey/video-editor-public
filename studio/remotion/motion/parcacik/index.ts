// parcacik ailesi (ADR 0045). Aile kartı bileşenlerini buraya ekler.
import type { Tanim } from "../cekirdek/tipler";
import konfeti from "./konfeti/Konfeti";
import parilti from "./parilti/Parilti";
import sokDalgasi from "./sok-dalgasi/SokDalgasi";
import yildizPatlama from "./yildiz-patlama/YildizPatlama";

export const PARCACIK: Tanim[] = [
  konfeti,
  parilti,
  sokDalgasi,
  yildizPatlama,
];
