// tipografi ailesi: kinetik tipografi, bölüm kapağı, fikir dönüşümü ve canlı durum rozetleri.
import type { Tanim } from "../cekirdek/tipler";
import bolumBaslik from "./bolum-baslik/BolumBaslik";
import durumRozeti from "./durum-rozeti/DurumRozeti";
import kayanKelime from "./kayan-kelime/KayanKelime";
import kinetikBaslik from "./kinetik-baslik/KinetikBaslik";
import vurguSoz from "./vurgu-soz/VurguSoz";

export const TIPOGRAFI: Tanim[] = [
  kinetikBaslik,
  bolumBaslik,
  vurguSoz,
  durumRozeti,
  kayanKelime,
];
