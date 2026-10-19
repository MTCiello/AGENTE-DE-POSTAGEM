import React from "react";
import { C } from "./theme";

// I.V.A. (Inteligência Visual Ativa) — computador antigo estilo IBM (monitor CRT sobre o gabinete
// com drives de disquete). Na tela, o rosto dela: um sorriso amigável ":)" em fósforo dourado.
// O LED de energia é o ponto dourado da CIELLO — ele vira o "Pontinho" e voa até o que ela mostra.
export const IVA_VB = { w: 420, h: 400 };
export const IVA_LED = { x: 322 / 420, y: 247 / 400 }; // posição relativa do LED (para o Pontinho)

export const Iva: React.FC<{
  frame: number; fps: number; size?: number; talking?: boolean;
  mood?: "idle" | "happy" | "think" | "surprise"; look?: [number, number]; ledOn?: boolean;
}> = ({ frame, fps, size = 300, talking = false, mood = "idle", look = [0, 0], ledOn = true }) => {
  const t = frame / fps;
  const blink = t % 3.4 < 0.1;
  const fx = 210 + look[0] * 14, fy = 138 + look[1] * 10;
  const open = talking ? 0.25 + 0.75 * Math.abs(Math.sin(t * 12.5)) * (0.55 + 0.45 * Math.abs(Math.sin(t * 4.7))) : 0;
  const flick = 0.92 + 0.08 * Math.sin(t * 37) * Math.sin(t * 11);
  const roll = ((t * 60) % 180) + 46; // faixa de varredura descendo pela tela
  const h = (size * IVA_VB.h) / IVA_VB.w;
  const gold = C.ouro;
  return (
    <svg width={size} height={h} viewBox={`0 0 ${IVA_VB.w} ${IVA_VB.h}`} style={{ overflow: "visible" }}>
      <defs>
        <radialGradient id="crt" cx="50%" cy="45%" r="70%">
          <stop offset="0%" stopColor="#2A2620" />
          <stop offset="70%" stopColor="#171613" />
          <stop offset="100%" stopColor="#0D0C0B" />
        </radialGradient>
        <filter id="phos" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="4" result="b" />
          <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <linearGradient id="beige" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#F1ECDF" />
          <stop offset="100%" stopColor="#DCD4C1" />
        </linearGradient>
        <linearGradient id="beigeBase" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#E6DFCD" />
          <stop offset="100%" stopColor="#CFC6B1" />
        </linearGradient>
        <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
          <rect width="4" height="2" fill="rgba(255,255,255,0.035)" />
        </pattern>
        <clipPath id="screenClip"><rect x="100" y="56" width="220" height="160" rx="30" /></clipPath>
      </defs>

      {/* gabinete (CPU) com drives de disquete */}
      <polygon points="36,292 384,292 372,276 48,276" fill="#EFE9DB" />
      <rect x="36" y="292" width="348" height="78" rx="8" fill="url(#beigeBase)" stroke="#BDB49E" strokeWidth="2" />
      <rect x="224" y="306" width="132" height="16" rx="4" fill="#3A3731" />
      <rect x="232" y="312" width="60" height="4" rx="2" fill="#57534A" />
      <rect x="224" y="334" width="132" height="16" rx="4" fill="#3A3731" />
      <rect x="232" y="340" width="60" height="4" rx="2" fill="#57534A" />
      {[0, 1, 2, 3, 4].map((i) => <rect key={i} x={58 + i * 16} y={314} width={8} height={36} rx={3} fill="#C9C0AA" />)}
      <text x="160" y="345" fontFamily="Oswald, sans-serif" fontWeight={600} fontSize="17" letterSpacing="3" fill="#6E685B">CIELLO</text>

      {/* pescoço */}
      <rect x="172" y="258" width="76" height="22" rx="4" fill="#CFC7B3" />

      {/* monitor */}
      <rect x="56" y="16" width="308" height="250" rx="28" fill="url(#beige)" stroke="#BDB49E" strokeWidth="2" />
      <path d="M340 30 Q364 30 364 56 L364 238 Q364 262 340 264 L332 264 L332 32 Z" fill="rgba(120,105,80,0.10)" />
      <rect x="84" y="40" width="252" height="190" rx="26" fill="#CDC4AF" />
      <rect x="100" y="56" width="220" height="160" rx="30" fill="url(#crt)" />
      <g clipPath="url(#screenClip)" opacity={flick}>
        <rect x="100" y="56" width="220" height="160" fill="url(#scan)" />
        <rect x="100" y={roll} width="220" height="14" fill="rgba(224,168,28,0.05)" />
        {/* rosto :) */}
        <g filter="url(#phos)">
          {mood === "happy" ? (
            <>
              <path d={`M${fx - 52} ${fy - 14} Q${fx - 36} ${fy - 34} ${fx - 20} ${fy - 14}`} stroke={gold} strokeWidth="9" fill="none" strokeLinecap="round" />
              <path d={`M${fx + 20} ${fy - 14} Q${fx + 36} ${fy - 34} ${fx + 52} ${fy - 14}`} stroke={gold} strokeWidth="9" fill="none" strokeLinecap="round" />
            </>
          ) : (
            [-1, 1].map((s) => {
              const eh = blink ? 4 : mood === "surprise" ? 30 : mood === "think" ? 16 : 24;
              return <rect key={s} x={fx + s * 36 - 8} y={fy - 22 - eh / 2 - (mood === "think" ? 6 : 0)} width="16" height={eh} rx="7" fill={gold} />;
            })
          )}
          {talking ? (
            <path d={`M${fx - 40} ${fy + 10} Q${fx} ${fy + 10 + 46 * open + 10} ${fx + 40} ${fy + 10} Z`} fill={gold} />
          ) : mood === "think" ? (
            <path d={`M${fx - 26} ${fy + 22} L${fx + 26} ${fy + 14}`} stroke={gold} strokeWidth="8" strokeLinecap="round" />
          ) : mood === "surprise" ? (
            <ellipse cx={fx} cy={fy + 24} rx="14" ry="16" fill="none" stroke={gold} strokeWidth="8" />
          ) : (
            <path d={`M${fx - 40} ${fy + 8} Q${fx} ${fy + (mood === "happy" ? 54 : 42)} ${fx + 40} ${fy + 8}`} stroke={gold} strokeWidth="9" fill="none" strokeLinecap="round" />
          )}
        </g>
        {/* reflexo do vidro */}
        <path d="M112 70 Q160 60 214 64 L200 82 Q154 78 116 88 Z" fill="rgba(255,255,255,0.07)" />
      </g>
      {/* grade de ventilação e LED (o ponto dourado) */}
      {[0, 1, 2, 3].map((i) => <rect key={i} x={98 + i * 14} y={240} width={8} height={14} rx={3} fill="#C7BEA8" />)}
      <circle cx="322" cy="247" r="8" fill={ledOn ? gold : "#8E8670"} />
      {ledOn && <circle cx="320" cy="245" r="3" fill="#FFF0BF" />}
    </svg>
  );
};

// o ponto dourado (LED da I.V.A.), com brilho
export const Pontinho: React.FC<{ x: number; y: number; r?: number; glow?: number }> = ({ x, y, r = 22, glow = 1 }) => (
  <div style={{ position: "absolute", left: x - r * 3, top: y - r * 3, width: r * 6, height: r * 6, pointerEvents: "none" }}>
    <div style={{ position: "absolute", inset: 0, borderRadius: "50%", background: `radial-gradient(circle, rgba(224,168,28,${0.55 * glow}) 0%, rgba(224,168,28,0) 65%)` }} />
    <div style={{ position: "absolute", left: r * 2, top: r * 2, width: r * 2, height: r * 2, borderRadius: "50%", background: `radial-gradient(circle at 35% 30%, #FFE7A3 0%, ${C.ouro} 45%, #B98A10 100%)`, boxShadow: "0 6px 14px rgba(80,60,10,0.35)" }} />
  </div>
);
