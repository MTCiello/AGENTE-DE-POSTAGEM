import React from "react";
import { interpolate } from "remotion";
import { C, F } from "./theme";

// Legenda karaokê (estilo do reel da escala 6x1): o trecho todo aparece em cinza claro e as
// palavras vão escurecendo conforme são faladas. Palavras entre *asteriscos* ganham grifo dourado.
export type Line = { from: number; to: number; text: string };

// tema "video": para cenas com filmagem/clone ao fundo — letras claras com sombra.
export const Karaoke: React.FC<{ frame: number; fps: number; lines: Line[]; y?: number; tema?: "claro" | "video" }> = ({ frame, fps, lines, y = 1350, tema = "claro" }) => {
  const [de, para] = tema === "video" ? ["#B9B4A8", C.papel] : [C.cinzaTexto, C.carvao];
  const sombra = tema === "video" ? "0 3px 14px rgba(0,0,0,0.75), 0 1px 2px rgba(0,0,0,0.9)" : "0 2px 0 rgba(255,255,255,0.35)";
  const t = frame / fps;
  const cur = lines.find((l) => t >= l.from && t < l.to);
  if (!cur) return null;
  const words = cur.text.split(" ");
  const total = words.reduce((a, w) => a + w.replace(/\*/g, "").length + 1, 0);
  let acc = 0;
  const span = (cur.to - cur.from) * 0.94;
  const fadeIn = interpolate(t - cur.from, [0, 0.18], [0, 1], { extrapolateRight: "clamp" });
  const lift = interpolate(t - cur.from, [0, 0.25], [18, 0], { extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", left: 80, right: 80, top: y, textAlign: "center", opacity: fadeIn, transform: `translateY(${lift}px)` }}>
      <div style={{ fontFamily: F.display, fontWeight: 600, fontSize: 68, lineHeight: 1.12, textTransform: "uppercase", letterSpacing: 1, textShadow: sombra }}>
        {words.map((w, i) => {
          const clean = w.replace(/\*/g, "");
          const hl = w.includes("*");
          const ws = cur.from + (acc / total) * span;
          acc += clean.length + 1;
          const spoken = interpolate(t, [ws - 0.05, ws + 0.12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const color = mix(de, para, spoken);
          return (
            <span key={i} style={{ color, position: "relative", display: "inline-block", marginRight: 16 }}>
              {clean}
              {hl ? (
                <span style={{ position: "absolute", left: -4, right: -4, bottom: 4, height: 12, background: C.ouro, transformOrigin: "left", transform: `scaleX(${spoken})`, zIndex: -1, borderRadius: 2 }} />
              ) : null}
            </span>
          );
        })}
      </div>
    </div>
  );
};

const hex = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
export const mix = (a: string, b: string, k: number) => {
  const A = hex(a), B = hex(b);
  return `rgb(${A.map((v, i) => Math.round(v + (B[i] - v) * k)).join(",")})`;
};
