import React from "react";
import { CLOUD_PATH } from "./cloudPath";
import { C } from "./theme";

// I.V.A. — a nuvem do logo com rosto. Coordenadas no viewBox do símbolo (878 x 481).
// O ponto dourado do logo (810, 411) é desenhado à parte pelo componente Pontinho.
const INNER =
  "M150 395 C92 372 82 300 124 262 C146 244 178 240 205 249 L242 260 L242 222 C242 150 296 92 352 92 C412 92 462 146 462 222 L463 258 L486 253 C528 241 552 244 572 256 C598 272 606 292 604 318 L604 396 Z";

export const Iva: React.FC<{
  frame: number; fps: number; size?: number; talking?: boolean;
  mood?: "idle" | "happy" | "think" | "surprise"; look?: [number, number];
}> = ({ frame, fps, size = 300, talking = false, mood = "idle", look = [0, 0] }) => {
  const t = frame / fps;
  const blink = t % 3.6 < 0.11 || (t % 3.6 > 0.25 && t % 3.6 < 0.33 && Math.floor(t / 3.6) % 2 === 0);
  const ex = 330 + look[0] * 22, ey = 305 + look[1] * 14;
  const open = talking ? 0.35 + 0.65 * Math.abs(Math.sin(t * 13)) * (0.6 + 0.4 * Math.abs(Math.sin(t * 5.3))) : 0;
  const h = (size * 481) / 878;
  return (
    <svg width={size} height={h} viewBox="0 0 878 481" style={{ overflow: "visible" }}>
      <path d={INNER} fill={C.carvao} />
      <path d={CLOUD_PATH} fill={C.papel} fillRule="evenodd" />
      {/* olhos */}
      {[-1, 1].map((s) => {
        const x = ex + s * 62;
        if (mood === "happy")
          return <path key={s} d={`M${x - 26} ${ey + 8} Q${x} ${ey - 26} ${x + 26} ${ey + 8}`} stroke={C.ouro} strokeWidth={14} fill="none" strokeLinecap="round" />;
        const eh = blink ? 6 : mood === "think" ? 34 : mood === "surprise" ? 62 : 52;
        return (
          <g key={s}>
            <rect x={x - 17} y={ey - eh / 2 - (mood === "think" ? 10 : 0)} width={34} height={eh} rx={17} fill={C.ouro} />
            {!blink && <circle cx={x - 6} cy={ey - eh / 4 - (mood === "think" ? 10 : 0)} r={6} fill="#FFF3CC" />}
          </g>
        );
      })}
      {/* boca */}
      {mood === "happy" && !talking ? (
        <path d={`M${ex - 30} ${ey + 52} Q${ex} ${ey + 80} ${ex + 30} ${ey + 52}`} stroke={C.ouro} strokeWidth={12} fill="none" strokeLinecap="round" />
      ) : (
        <rect x={ex - 24 - open * 6} y={ey + 54 - open * 12} width={48 + open * 12} height={8 + open * 26} rx={10} fill={C.ouro} />
      )}
    </svg>
  );
};

// o ponto dourado do logo, com brilho
export const Pontinho: React.FC<{ x: number; y: number; r?: number; glow?: number }> = ({ x, y, r = 22, glow = 1 }) => (
  <div style={{ position: "absolute", left: x - r * 3, top: y - r * 3, width: r * 6, height: r * 6, pointerEvents: "none" }}>
    <div style={{ position: "absolute", inset: 0, borderRadius: "50%", background: `radial-gradient(circle, rgba(224,168,28,${0.55 * glow}) 0%, rgba(224,168,28,0) 65%)` }} />
    <div style={{ position: "absolute", left: r * 2, top: r * 2, width: r * 2, height: r * 2, borderRadius: "50%", background: `radial-gradient(circle at 35% 30%, #FFE7A3 0%, ${C.ouro} 45%, #B98A10 100%)`, boxShadow: "0 6px 14px rgba(80,60,10,0.35)" }} />
  </div>
);
