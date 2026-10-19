import React from "react";
import { AbsoluteFill, CalculateMetadataFunction, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { C, F } from "./theme";
import { Karaoke, Line } from "./Captions";
import { EndCard, EndLayer, Pill, kf, sp } from "./common";

// Reel montado com clipes do clone digital (InfiniteTalk, Wan 2.2, Wan-Animate…).
// Tudo vem de uma "montagem" JSON (ver src/montagens/), então um reel novo não precisa de código:
// os clipes ficam em reels/public/clone/ e a narração entra depois, no central/mixar.py.

export type CenaClone = {
  video?: string; // caminho dentro de reels/public (ex.: "clone/fala-1.mp4"); sem vídeo vira um quadro de rascunho
  de: number; // segundos no reel
  ate: number;
  inicioClip?: number; // de onde o clipe começa, em segundos
  zoom?: [number, number]; // zoom lento do começo ao fim da cena
  rotulo?: [string, string?]; // pílula no topo: texto e destaque em ouro
  nota?: string; // descrição da cena, aparece só no rascunho
};

export type MontagemClone = {
  total: number;
  cenas: CenaClone[];
  falas: Line[];
  fim?: { inicio: number; produto: string; palavra: string; sub: string; rodape: [string, string] };
};

export const calcularClone: CalculateMetadataFunction<MontagemClone> = ({ props }) => ({
  durationInFrames: Math.round(props.total * 30),
});

const Rascunho: React.FC<{ cena: CenaClone; i: number }> = ({ cena, i }) => (
  <AbsoluteFill style={{ background: `linear-gradient(160deg, ${C.carvao2}, ${C.azul})`, alignItems: "center", justifyContent: "center", padding: 120 }}>
    <div style={{ fontFamily: F.display, fontSize: 36, letterSpacing: 10, color: C.ouro }}>CENA {i + 1} · CLONE</div>
    <div style={{ marginTop: 30, fontFamily: F.ui, fontSize: 44, lineHeight: 1.3, color: C.papel, textAlign: "center" }}>{cena.nota ?? "clipe ainda não gerado"}</div>
    <div style={{ marginTop: 30, fontFamily: F.ui, fontSize: 30, color: C.cinza }}>{cena.video ?? "sem arquivo"}</div>
  </AbsoluteFill>
);

const Cena: React.FC<{ cena: CenaClone; i: number }> = ({ cena, i }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const dur = cena.ate - cena.de;
  const t = frame / fps;
  const [z0, z1] = cena.zoom ?? [1.0, 1.06];
  const zoom = kf(t, [[0, z0], [dur, z1]]);
  const entra = kf(t, [[0, 0], [0.2, 1]]); // corte suave entre cenas
  const rot = cena.rotulo ? sp(frame, fps, 0.15) * kf(t, [[dur - 0.3, 1], [dur, 0]]) : 0;
  return (
    <AbsoluteFill style={{ opacity: i === 0 ? 1 : entra }}>
      <AbsoluteFill style={{ transform: `scale(${zoom})` }}>
        {cena.video ? (
          <OffthreadVideo src={staticFile(cena.video)} muted startFrom={Math.round((cena.inicioClip ?? 0) * fps)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        ) : (
          <Rascunho cena={cena} i={i} />
        )}
      </AbsoluteFill>
      {cena.rotulo ? <Pill a={cena.rotulo[0]} b={cena.rotulo[1]} p={rot} top={170} size={38} /> : null}
    </AbsoluteFill>
  );
};

export const CloneReel: React.FC<MontagemClone> = ({ cenas, falas, fim }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const endP = fim ? kf(t, [[fim.inicio, 0], [fim.inicio + 0.35, 1]]) : 0;
  return (
    <AbsoluteFill style={{ background: C.carvao }}>
      {cenas.map((c, i) => (
        <Sequence key={i} from={Math.round(c.de * fps)} durationInFrames={Math.max(1, Math.round((c.ate - c.de) * fps))}>
          <Cena cena={c} i={i} />
        </Sequence>
      ))}
      {/* escurece a base para a legenda ler bem sobre qualquer filmagem */}
      <AbsoluteFill style={{ top: 1100, background: "linear-gradient(180deg, rgba(22,22,22,0) 0%, rgba(22,22,22,0.55) 45%, rgba(22,22,22,0.8) 100%)", opacity: 1 - endP }} />
      <div style={{ opacity: 1 - endP }}><Karaoke frame={frame} fps={fps} lines={falas} y={1420} tema="video" /></div>
      {fim ? (
        <EndLayer p={endP}>
          <EndCard frame={frame - Math.round(fim.inicio * fps)} fps={fps} product={fim.produto} word={fim.palavra} sub={fim.sub} foot={fim.rodape} />
        </EndLayer>
      ) : null}
    </AbsoluteFill>
  );
};
