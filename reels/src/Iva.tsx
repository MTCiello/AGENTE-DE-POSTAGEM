import React from "react";

// I.V.A. (Inteligência Visual Ativa) — fiel ao protótipo original:
// computador retrô azul-marinho em 3/4, tela CRT com rosto ciano brilhante (olhos "O O" e um
// sorrisinho), painel lateral turquesa com botões e um botão laranja, gabinete com disquete
// turquesa saindo do drive. O botão laranja é o "Pontinho": ele se solta e aponta as coisas.
export const IVA_VB = { w: 520, h: 470 };
export const IVA_LED = { x: 373 / 520, y: 282 / 470 };
export const IVA_ORANGE = "#F26B24";

const NAVY = "#2D3884", NAVY_D = "#1F2766", NAVY_DD = "#161C4D", NAVY_L = "#4352A6";
const TEAL = "#1FB7B4", TEAL_L = "#3FD9D2", CYAN = "#3CF5F0", SCREEN = "#3A4D57";

export const Iva: React.FC<{
  frame: number; fps: number; size?: number; talking?: boolean;
  mood?: "idle" | "happy" | "think" | "surprise"; look?: [number, number]; ledOn?: boolean; floppy?: number;
}> = ({ frame, fps, size = 300, talking = false, mood = "idle", look = [0, 0], ledOn = true, floppy }) => {
  const t = frame / fps;
  const blink = t % 3.3 < 0.1;
  const lx = look[0] * 12, ly = look[1] * 8;
  const open = talking ? 0.2 + 0.8 * Math.abs(Math.sin(t * 12.5)) * (0.55 + 0.45 * Math.abs(Math.sin(t * 4.3))) : 0;
  const glow = 0.85 + 0.15 * Math.sin(t * 3) + 0.05 * Math.sin(t * 41);
  const fl = floppy ?? (0.5 + 0.5 * Math.sin(t * 0.9)) * 0.25 + 0.75; // disquete entra/sai de leve
  const h = (size * IVA_VB.h) / IVA_VB.w;
  const ex = [150 + lx, 240 + lx], ey = 162 + ly;
  return (
    <svg width={size} height={h} viewBox={`0 0 ${IVA_VB.w} ${IVA_VB.h}`} style={{ overflow: "visible" }}>
      <defs>
        <linearGradient id="ivFront" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stopColor="#36429A" /><stop offset="100%" stopColor={NAVY} /></linearGradient>
        <linearGradient id="ivTop" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#5465B8" /><stop offset="100%" stopColor={NAVY_L} /></linearGradient>
        <radialGradient id="ivScreen" cx="45%" cy="40%" r="75%"><stop offset="0%" stopColor="#4C636C" /><stop offset="70%" stopColor={SCREEN} /><stop offset="100%" stopColor="#26343C" /></radialGradient>
        <radialGradient id="ivAura" cx="50%" cy="50%" r="50%"><stop offset="0%" stopColor="rgba(60,245,240,0.28)" /><stop offset="100%" stopColor="rgba(60,245,240,0)" /></radialGradient>
        <filter id="ivGlow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="5" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
        <filter id="ivSoft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2" /></filter>
        <clipPath id="ivClip"><rect x="80" y="82" width="236" height="200" rx="34" /></clipPath>
      </defs>

      {/* ---------- gabinete ---------- */}
      <polygon points="12,356 62,330 506,330 456,356" fill="url(#ivTop)" />
      <polygon points="456,356 506,330 506,414 456,444" fill={NAVY_DD} />
      {Array.from({ length: 9 }).map((_, i) => <line key={i} x1={466} y1={370 + i * 7} x2={498} y2={352 + i * 7} stroke="#11163C" strokeWidth={3} />)}
      <rect x="12" y="356" width="444" height="88" rx="10" fill="url(#ivFront)" />
      <rect x="26" y="370" width="416" height="60" rx="6" fill="none" stroke={NAVY_DD} strokeWidth="4" />
      <rect x="40" y="386" width="16" height="13" rx="2" fill="#D21E34" />
      <rect x="60" y="386" width="16" height="13" rx="2" fill={TEAL} />
      <rect x="128" y="384" width="176" height="9" rx="3" fill="#0E1236" />
      <circle cx="318" cy="390" r="3" fill="#0E1236" />
      <rect x="334" y="392" width="40" height="12" rx="3" fill="#121638" /><rect x="388" y="396" width="40" height="12" rx="3" fill="#121638" />
      {/* disquete saindo do drive */}
      <g transform={`translate(${(1 - fl) * 60},0)`}>
        <polygon points="118,393 306,393 296,424 104,424" fill={TEAL} />
        <polygon points="118,393 306,393 304,399 116,399" fill={TEAL_L} />
        <ellipse cx="205" cy="404" rx="30" ry="7" fill="#1A5E61" />
        <rect x="140" y="408" width="44" height="10" rx="2" fill="#1A5E61" />
      </g>

      {/* ---------- monitor ---------- */}
      <rect x="96" y="318" width="292" height="26" fill={NAVY_DD} />
      {Array.from({ length: 22 }).map((_, i) => <rect key={i} x={104 + i * 13} y={322} width={6} height={18} fill="#10153D" />)}
      <rect x="450" y="58" width="34" height="210" rx="10" fill={NAVY_DD} />
      <polygon points="436,40 474,14 474,292 436,322" fill={NAVY_D} />
      <polygon points="50,40 92,14 474,14 436,40" fill="url(#ivTop)" />
      <rect x="40" y="38" width="398" height="286" rx="22" fill="url(#ivFront)" />
      <rect x="58" y="58" width="276" height="248" rx="26" fill={NAVY_D} />
      <rect x="66" y="66" width="262" height="232" rx="30" fill={NAVY_DD} />
      <rect x="80" y="82" width="236" height="200" rx="34" fill="url(#ivScreen)" />
      <g clipPath="url(#ivClip)">
        <ellipse cx="198" cy="182" rx="150" ry="120" fill="url(#ivAura)" opacity={glow} />
        {Array.from({ length: 50 }).map((_, i) => <rect key={i} x={80} y={82 + i * 4} width={236} height={1.4} fill="rgba(255,255,255,0.035)" />)}
        {/* rosto */}
        <g filter="url(#ivGlow)" opacity={glow}>
          {mood === "happy" ? (
            ex.map((x, i) => <path key={i} d={`M${x - 22} ${ey + 6} Q${x} ${ey - 34} ${x + 22} ${ey + 6}`} stroke={CYAN} strokeWidth="11" fill="none" strokeLinecap="round" />)
          ) : (
            ex.map((x, i) => {
              const ry = blink ? 3 : mood === "surprise" ? 38 : mood === "think" ? 22 : 32;
              const dy = mood === "think" ? -10 : 0;
              return blink ? <line key={i} x1={x - 20} y1={ey} x2={x + 20} y2={ey} stroke={CYAN} strokeWidth="9" strokeLinecap="round" />
                : <ellipse key={i} cx={x + (mood === "think" ? 6 : 0)} cy={ey + dy} rx={20} ry={ry} fill="none" stroke={CYAN} strokeWidth="11" />;
            })
          )}
          {talking ? (
            <path d={`M${195 + lx - 26} ${ey + 62} Q${195 + lx} ${ey + 62 + 10 + 34 * open} ${195 + lx + 26} ${ey + 62} Q${195 + lx} ${ey + 62 + 4 * open} ${195 + lx - 26} ${ey + 62} Z`} fill={CYAN} />
          ) : mood === "think" ? (
            <line x1={180 + lx} y1={ey + 70} x2={212 + lx} y2={ey + 64} stroke={CYAN} strokeWidth="9" strokeLinecap="round" />
          ) : mood === "surprise" ? (
            <ellipse cx={195 + lx} cy={ey + 72} rx="12" ry="14" fill="none" stroke={CYAN} strokeWidth="8" />
          ) : (
            <path d={`M${195 + lx - 24} ${ey + 60} Q${195 + lx} ${ey + (mood === "happy" ? 92 : 82)} ${195 + lx + 24} ${ey + 60}`} stroke={CYAN} strokeWidth="9" fill="none" strokeLinecap="round" />
          )}
        </g>
        <path d="M96 100 Q150 88 222 92 L206 112 Q150 108 100 120 Z" fill="rgba(255,255,255,0.06)" />
      </g>
      {/* painel lateral turquesa */}
      <rect x="346" y="62" width="70" height="80" rx="4" fill={TEAL} />
      <rect x="370" y="98" width="24" height="6" rx="2" fill="#137F7D" />
      <rect x="352" y="154" width="58" height="22" rx="3" fill={NAVY_DD} />
      <rect x="364" y="161" width="24" height="9" rx="2" fill={TEAL_L} />
      <rect x="346" y="188" width="70" height="122" rx="4" fill={TEAL} />
      {[0, 1, 2].map((i) => <rect key={i} x="363" y={204 + i * 22} width="22" height="14" rx="3" fill={TEAL_L} stroke="#138F8C" strokeWidth="2" />)}
      <circle cx="373" cy="282" r="12" fill={ledOn ? IVA_ORANGE : "#9C5D3C"} />
      {ledOn && <circle cx="369" cy="278" r="4" fill="#FFC29E" />}
      {/* brilho de contorno (rim light) */}
      <path d="M62 38 L416 38" stroke="rgba(255,255,255,0.18)" strokeWidth="3" filter="url(#ivSoft)" />
    </svg>
  );
};

// o botão laranja da I.V.A., quando sai voando para apontar
export const Pontinho: React.FC<{ x: number; y: number; r?: number; glow?: number }> = ({ x, y, r = 22, glow = 1 }) => (
  <div style={{ position: "absolute", left: x - r * 3, top: y - r * 3, width: r * 6, height: r * 6, pointerEvents: "none" }}>
    <div style={{ position: "absolute", inset: 0, borderRadius: "50%", background: `radial-gradient(circle, rgba(242,107,36,${0.5 * glow}) 0%, rgba(242,107,36,0) 65%)` }} />
    <div style={{ position: "absolute", left: r * 2, top: r * 2, width: r * 2, height: r * 2, borderRadius: "50%", background: `radial-gradient(circle at 35% 30%, #FFC7A6 0%, ${IVA_ORANGE} 45%, #B9461A 100%)`, boxShadow: "0 6px 14px rgba(90,40,10,0.35)" }} />
  </div>
);
