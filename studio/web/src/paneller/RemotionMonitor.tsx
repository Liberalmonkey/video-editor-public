// Program monitörünün Remotion yolu (son çare, ADR 0051). Ayrı parça: Remotion ve three.js yalnız bu yol seçilince iner (ADR 0057).
import { Player, type PlayerRef } from "@remotion/player";
import React from "react";
import { Kurgu } from "../../../remotion/Kurgu";
import type { KurguProps } from "../../../remotion/tipler";

type Ozellik = {
  girdi: KurguProps;
  fps: number;
  sureKare: number;
  ilkKare: number;
  hiz: number;
  stil: React.CSSProperties;
};

const RemotionMonitor = React.forwardRef<PlayerRef, Ozellik>(({ girdi, fps, sureKare, ilkKare, hiz, stil }, ref) => (
  <Player ref={ref} component={Kurgu as React.FC<any>} inputProps={girdi}
    compositionWidth={girdi.sekans.w} compositionHeight={girdi.sekans.h} fps={fps}
    durationInFrames={sureKare} playbackRate={hiz} initialFrame={ilkKare}
    clickToPlay={false} doubleClickToFullscreen={false} spaceKeyToPlayOrPause={false} moveToBeginningWhenEnded={false}
    style={stil} />
));

export default RemotionMonitor;
