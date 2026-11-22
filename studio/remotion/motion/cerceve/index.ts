// cerceve ailesi (ADR 0045). Aile kartı bileşenlerini buraya ekler.
import type { Tanim } from "../cekirdek/tipler";
import bant from "./bant/Bant";
import kagit from "./kagit/Kagit";
import polaroid from "./polaroid/Polaroid";
import tarayici from "./tarayici/Tarayici";
import telefon from "./telefon/Telefon";
import yirtik from "./yirtik/Yirtik";

export const CERCEVE: Tanim[] = [
  telefon,
  tarayici,
  polaroid,
  bant,
  kagit,
  yirtik,
];
