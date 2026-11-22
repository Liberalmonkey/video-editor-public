// kart ailesi (ADR 0045). Aile kartı bileşenlerini buraya ekler.
import type { Tanim } from "../cekirdek/tipler";
import abone from "./abone/Abone";
import alinti from "./alinti/Alinti";
import altbantBlok from "./altbant-blok/AltbantBlok";
import altbantCizgi from "./altbant-cizgi/AltbantCizgi";
import altbantKonu from "./altbant-konu/AltbantKonu";
import bildirim from "./bildirim/Bildirim";
import cip from "./cip/Cip";
import ctaKarti from "./cta-karti/CtaKarti";
import kart from "./kart/Kart";

export const KART: Tanim[] = [
  altbantCizgi,
  altbantBlok,
  altbantKonu,
  cip,
  kart,
  alinti,
  bildirim,
  abone,
  ctaKarti,
];
