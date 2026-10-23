import React from "react";
import { AbsoluteFill, Easing, interpolate, spring } from "remotion";
import "@fontsource/inter/800.css";
import "@fontsource/inter/900.css";
import { C, F } from "../theme";
import { CLOUD_PATH } from "../cloudPath";

// Kit do "plano-sequência" da Ciello: movimentos medidos, tudo função do tempo (t em segundos).
// Princípios (estudados do onetake e do reel de referência, implementação nossa):
// fundo calmo + elementos pequenos que se animam; uma virada grande a cada 3–5 s;
// algo sempre continua de uma cena para a outra; a câmera antecipa, pousa e balança de leve.

export const PAPEL = { claro: "#F4EFE4", meio: "#ECE5D7", borda: "#E0D8C7", traco: "#B8AD98" };
export const TXT = { escuro: "#1E1C19", medio: "#5E584E", leve: "#8F877A" };

const suave = Easing.bezier(0.65, 0, 0.35, 1);
export const entre = (t: number, a: number, b: number, e = suave) =>
  interpolate(t, [a, b], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: e });
export const mola = (t: number, fps: number, at: number, damping = 14, stiffness = 130) =>
  spring({ frame: Math.round((t - at) * fps), fps, config: { damping, stiffness, mass: 0.9 } });
export const mix = (a: number, b: number, k: number) => a + (b - a) * k;

// ------------------------------------------------------------------ fundo: papel + horizonte de Chapecó em traço
const PREDIOS = [
  [0, 120], [70, 210], [130, 160], [200, 300], [260, 190], [330, 250], [400, 140], [470, 340], [520, 0], [600, 230],
  [660, 170], [720, 280], [790, 150], [850, 220], [920, 260], [990, 180], [1040, 140],
];
export const Papel: React.FC<{ t: number; marca?: string }> = ({ t, marca = "@ciellotec" }) => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse 85% 60% at 50% 38%, ${PAPEL.claro} 0%, ${PAPEL.meio} 62%, ${PAPEL.borda} 100%)` }}>
    <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
      <g stroke={PAPEL.traco} strokeWidth={2} fill="none" opacity={0.55} transform={`translate(${-Math.sin(t * 0.15) * 6}, 0)`}>
        {PREDIOS.map(([x, h], i) =>
          h === 0 ? ( // catedral: torre com cruz
            <g key={i}>
              <path d={`M${x} 1790 V1520 L${x + 30} 1470 L${x + 60} 1520 V1790`} />
              <path d={`M${x + 30} 1470 V1430 M${x + 18} 1446 H${x + 42}`} />
            </g>
          ) : (
            <g key={i}>
              <rect x={x} y={1790 - h} width={58} height={h} />
              {Array.from({ length: Math.floor(h / 40) }).map((_, j) => (
                <path key={j} d={`M${x + 12} ${1790 - h + 24 + j * 40} h10 M${x + 34} ${1790 - h + 24 + j * 40} h10`} />
              ))}
            </g>
          ),
        )}
        <path d="M0 1790 H1080" />
      </g>
    </svg>
    <div style={{ position: "absolute", bottom: 210, width: "100%", textAlign: "center", fontFamily: F.ui, fontSize: 22, letterSpacing: 4, color: PAPEL.traco, opacity: 0.8 }}>
      {marca}
    </div>
  </AbsoluteFill>
);

// ------------------------------------------------------------------ texto cinético (palavra a palavra; *destaque* em ouro)
export const Cinetico: React.FC<{
  t: number; fps: number; texto: string; inicio: number; porPalavra?: number; x?: number; y: number; largura?: number;
  tamanho?: number; peso?: number; cor?: string; alinhar?: "left" | "center"; sai?: number; riscado?: number; corRisco?: string;
}> = ({ t, fps, texto, inicio, porPalavra = 0.13, x = 80, y, largura = 920, tamanho = 76, peso = 800, cor = TXT.escuro, alinhar = "left", sai, riscado = 0, corRisco = TXT.escuro }) => {
  const palavras = texto.split(" ");
  const saida = sai !== undefined ? entre(t, sai, sai + 0.35) : 0;
  return (
    <div style={{ position: "absolute", left: x, top: y, width: largura, textAlign: alinhar, fontFamily: "Inter, sans-serif", fontWeight: peso,
      fontSize: tamanho, lineHeight: 1.08, letterSpacing: -1.5, opacity: 1 - saida, transform: `translateY(${-saida * 40}px)` }}>
      <span style={{ position: "relative" }}>
        {palavras.map((p, i) => {
          const k = mola(t, fps, inicio + i * porPalavra, 16, 170);
          const destaque = p.includes("*");
          return (
            <span key={i} style={{ display: "inline-block", marginRight: tamanho * 0.24, opacity: Math.min(1, k * 1.4),
              transform: `translateY(${(1 - k) * 22}px)`, filter: `blur(${(1 - Math.min(1, k)) * 6}px)`,
              color: riscado > 0 ? mixCor(destaque ? C.ouro : cor, "#8A847A", riscado) : destaque ? C.ouro : cor }}>
              {p.replace(/\*/g, "")}
            </span>
          );
        })}
        {riscado > 0 ? (
          <span style={{ position: "absolute", left: -8, top: "52%", height: tamanho * 0.09, width: `calc(${riscado * 100}% + 16px)`, background: corRisco, borderRadius: 4 }} />
        ) : null}
      </span>
    </div>
  );
};

const hex = (h: string) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
export const mixCor = (a: string, b: string, k: number) => {
  const A = hex(a), B = hex(b);
  return `rgb(${A.map((v, i) => Math.round(v + (B[i] - v) * k)).join(",")})`;
};

// ------------------------------------------------------------------ peças
export const Sombra = "0 18px 40px rgba(70,55,30,0.16), 0 3px 8px rgba(70,55,30,0.10)";

export const Bloco: React.FC<{ x: number; y: number; tam: number; k: number; children: React.ReactNode }> = ({ x, y, tam, k, children }) => (
  <div style={{ position: "absolute", left: x - tam / 2, top: y - tam / 2, width: tam, height: tam, borderRadius: tam * 0.26, background: "#FFFFFF",
    boxShadow: Sombra, display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${k})`, opacity: Math.min(1, k * 2) }}>
    {children}
  </div>
);

export const MarcaCiello: React.FC<{ largura: number; ponto?: number }> = ({ largura, ponto = 1 }) => (
  <svg width={largura} height={(largura * 481) / 878} viewBox="0 0 878 481">
    <path d={CLOUD_PATH} fill={C.carvao} fillRule="evenodd" />
    <circle cx={810} cy={411} r={67 * ponto} fill={C.ouro} />
  </svg>
);

export const IconeConversa: React.FC<{ tam: number }> = ({ tam }) => (
  <svg width={tam} height={tam} viewBox="0 0 64 64">
    <path d="M32 8C17.6 8 7 17.8 7 30.5c0 6.6 3 12.4 7.9 16.5L12 57l11.8-5.6c2.6.8 5.3 1.1 8.2 1.1 14.4 0 25-9.8 25-22S46.4 8 32 8z" fill={C.verde} />
    <circle cx={22} cy={31} r={3.6} fill="#fff" /><circle cx={32} cy={31} r={3.6} fill="#fff" /><circle cx={42} cy={31} r={3.6} fill="#fff" />
  </svg>
);

export const Pilula: React.FC<{ x: number; y: number; k: number; texto: string; tipo?: "ok" | "nao" | "ouro"; tam?: number; giro?: number; centro?: boolean }> = ({
  x, y, k, texto, tipo = "ok", tam = 30, giro = 0, centro,
}) => {
  const fundo = tipo === "ouro" ? C.ouro : "#FFFFFF";
  const cor = tipo === "ouro" ? C.carvao : TXT.escuro;
  const icone = tipo === "ok" ? ["✓", C.verde] : tipo === "nao" ? ["✕", C.vermelho] : null;
  return (
    <div style={{ position: "absolute", left: x, top: y, transform: `translate(${centro ? "-50%" : "0"}, 0) scale(${k}) rotate(${giro}deg)`, transformOrigin: "left center",
      opacity: Math.min(1, k * 2), background: fundo, color: cor, borderRadius: 999, padding: `${tam * 0.42}px ${tam * 0.8}px`, boxShadow: Sombra,
      fontFamily: "Inter, sans-serif", fontWeight: 800, fontSize: tam, display: "flex", alignItems: "center", gap: tam * 0.4, whiteSpace: "nowrap" }}>
      {icone ? (
        <span style={{ width: tam * 1.05, height: tam * 1.05, borderRadius: "50%", background: icone[1], color: "#fff", fontSize: tam * 0.62, display: "flex", alignItems: "center", justifyContent: "center" }}>{icone[0]}</span>
      ) : null}
      {texto}
    </div>
  );
};

export const Contador: React.FC<{ t: number; de: number; ate: number; a: number; b: number; prefixo?: string }> = ({ t, de, ate, a, b, prefixo = "" }) => (
  <>{prefixo}{Math.round(mix(de, ate, entre(t, a, b, Easing.out(Easing.cubic)))).toLocaleString("pt-BR")}</>
);

// janela que nasce de um card branco (morph 0 = card em branco, 1 = janela escura)
export const Janela: React.FC<{ x: number; y: number; w: number; h: number; morph: number; titulo: string; children?: React.ReactNode; estilo?: React.CSSProperties }> = ({
  x, y, w, h, morph, titulo, children, estilo,
}) => (
  <div style={{ position: "absolute", left: x, top: y, width: w, height: h, borderRadius: 26, overflow: "hidden", boxShadow: "0 40px 80px rgba(40,30,15,0.28)",
    background: mixCor("#FFFFFF", "#1A1918", morph), ...estilo }}>
    <div style={{ height: 58, display: "flex", alignItems: "center", gap: 12, padding: "0 24px", opacity: morph, borderBottom: "1px solid #2c2a28" }}>
      {["#FF5F57", "#FEBC2E", "#28C840"].map((c) => <span key={c} style={{ width: 16, height: 16, borderRadius: "50%", background: c }} />)}
      <span style={{ marginLeft: 16, fontFamily: F.ui, fontSize: 22, color: "#8E897E" }}>{titulo}</span>
    </div>
    <div style={{ opacity: entre(morph, 0.6, 1) }}>{children}</div>
  </div>
);

export const CardLegenda: React.FC<{ x: number; y: number; w: number; k: number; children: React.ReactNode }> = ({ x, y, w, k, children }) => (
  <div style={{ position: "absolute", left: x, top: y, width: w, minHeight: 120, borderRadius: 24, background: "#FFFDF8", boxShadow: Sombra, padding: "26px 34px",
    opacity: Math.min(1, k * 2), transform: `translateY(${(1 - k) * 30}px)` }}>
    {children}
  </div>
);

// câmera operada: escala/translada o palco, com balanço de mão e tranco ao pousar
export const camera = (t: number, chaves: [number, number, number, number][], pousos: number[] = []) => {
  // chaves: [tempo, x, y, zoom]
  let x = chaves[0][1], y = chaves[0][2], z = chaves[0][3];
  for (let i = 1; i < chaves.length; i++) {
    const [ta, , , ] = chaves[i - 1];
    const [tb, xb, yb, zb] = chaves[i];
    const k = entre(t, ta, tb);
    if (t >= ta) { x = mix(chaves[i - 1][1], xb, k); y = mix(chaves[i - 1][2], yb, k); z = mix(chaves[i - 1][3], zb, k); }
  }
  const mao = Math.sin(t * 0.9) * 3 + Math.sin(t * 1.7) * 2;
  const tranco = pousos.reduce((s, p) => s + (t > p && t < p + 0.35 ? Math.sin((t - p) * 40) * 6 * (1 - (t - p) / 0.35) : 0), 0);
  return `translate(${-x + mao}px, ${-y + tranco + mao * 0.6}px) scale(${z})`;
};

// rastro: desfoque proporcional à velocidade (imita o obturador)
export const rastro = (v: number) => `blur(${Math.min(10, Math.abs(v) * 0.6)}px)`;
