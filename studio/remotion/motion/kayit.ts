// Native motion kayıt tablosu (ADR 0045). Tek sahibi Claude'dur; aileler kendi index.ts dosyasına ekler.
import type { Tanim } from "./cekirdek/tipler";
import { CERCEVE } from "./cerceve";
import { CIZIM } from "./cizim";
import { DIS } from "./dis";
import { GECIS } from "./gecis";
import { IKON } from "./ikon";
import { KART } from "./kart";
import { PARCACIK } from "./parcacik";
import { TIPOGRAFI } from "./tipografi";
import { VERI } from "./veri";
import { ZEMIN } from "./zemin";

export const TUMU: Tanim[] = [...IKON, ...CIZIM, ...KART, ...TIPOGRAFI, ...VERI, ...CERCEVE, ...PARCACIK, ...ZEMIN, ...GECIS, ...DIS];

export const KAYIT: Record<string, Tanim> = Object.fromEntries(TUMU.map((t) => [t.meta.ad, t]));
