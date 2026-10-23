import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import "@fontsource/anton/400.css";
import "@fontsource/source-serif-4/400-italic.css";
import { C, F } from "./theme";
import { Iva } from "./Iva";
import { CLOUD_PATH } from "./cloudPath";

// Capa do reel (1080x1920). O que importa fica na faixa central 3:4 (y 240–1680),
// que é o recorte que aparece na grade do perfil do Instagram.

export type Cor = "marfim" | "cinza" | "ouro" | "vermelho";
export type DadosCapa = {
  tema?: "carvao" | "creme";
  tag?: string; // pílula no topo (ex.: "IA PRO SEU NEGÓCIO")
  linhas: [string, Cor][]; // título, linha a linha, com a cor de cada uma (mesmo formato do gancho do roteiro)
  apoio?: string; // frase menor embaixo do título (ex.: "Salva esse vídeo")
  selo?: string; // número/selo em destaque (ex.: "3 COMANDOS")
  iva?: "idle" | "happy" | "think" | "surprise" | "wave" | null; // null tira a I.V.A.
  foto?: string; // imagem em reels/public (ex.: o seu clone) no lugar da I.V.A.
  marca?: string; // nome no rodapé (o capa.mjs lê de comercial/empresa.json)
};

const TONS = {
  carvao: { fundo: C.carvao, luz: "rgba(224,168,28,0.20)", marfim: C.papel, cinza: "#8F8A80", tag: C.papel, apoio: "#CFC9BC", logo: C.papel },
  creme: { fundo: C.creme, luz: "rgba(255,255,255,0.65)", marfim: C.carvao, cinza: "#8A857A", tag: C.carvao, apoio: "#4A4740", logo: C.carvao },
};

// Anton em caixa alta tem ~0,5 em de largura por caractere: ajusta o corpo para a linha mais longa caber em 920 px.
const corpo = (linhas: [string, Cor][]) => {
  const maior = Math.max(...linhas.map(([t]) => t.length));
  return Math.min(210, Math.floor(920 / (0.5 * maior)));
};

export const Capa: React.FC<DadosCapa> = ({ tema = "carvao", tag, linhas, apoio, selo, iva = "happy", foto, marca = "" }) => {
  const k = TONS[tema];
  const cor = (c: Cor) => (c === "ouro" ? C.ouro : c === "vermelho" ? C.vermelho : k[c]);
  const fs = corpo(linhas);
  const mood = iva === "wave" ? "happy" : iva;
  return (
    <AbsoluteFill style={{ background: k.fundo, overflow: "hidden" }}>
      {/* luz quente e textura */}
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 70% 45% at 30% 30%, ${k.luz} 0%, rgba(0,0,0,0) 70%)` }} />
      <svg width={1080} height={1920} style={{ position: "absolute", opacity: tema === "carvao" ? 0.09 : 0.05, mixBlendMode: "overlay" }}>
        <filter id="grao"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" /></filter>
        <rect width="100%" height="100%" filter="url(#grao)" />
      </svg>

      {foto ? (
        <>
          <Img src={staticFile(foto)} style={{ position: "absolute", left: 0, top: 640, width: 1080, height: 1280, objectFit: "cover" }} />
          <AbsoluteFill style={{ background: `linear-gradient(180deg, ${k.fundo} 34%, rgba(0,0,0,0) 52%, rgba(0,0,0,0) 80%, ${k.fundo} 100%)` }} />
        </>
      ) : null}

      {/* bloco do título centralizado entre o topo da área 3:4 e a I.V.A. */}
      <div style={{ position: "absolute", top: 260, height: 1000, left: 80, right: 80, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "flex-start" }}>
        {tag ? (
          <div style={{ border: `3px solid ${C.ouro}`, borderRadius: 40, padding: "12px 30px", fontFamily: F.display, fontWeight: 600, fontSize: 34, letterSpacing: 6, color: k.tag, marginBottom: 40 }}>
            {tag.toUpperCase()}
          </div>
        ) : null}
        {linhas.map(([t, c], i) => (
          <div key={i} style={{ fontFamily: "Anton, Oswald, sans-serif", fontSize: fs, lineHeight: 1.02, color: cor(c), textTransform: "uppercase", letterSpacing: 1, whiteSpace: "nowrap" }}>
            {t}
          </div>
        ))}
        {apoio ? <div style={{ marginTop: 34, fontFamily: "'Source Serif 4', Georgia, serif", fontStyle: "italic", fontSize: 54, color: k.apoio }}>{apoio}</div> : null}
      </div>

      {selo ? (
        <div style={{ position: "absolute", left: 80, top: 1330, background: C.ouro, color: C.carvao, borderRadius: 18, padding: "18px 30px", fontFamily: "Anton, Oswald, sans-serif", fontSize: 64, letterSpacing: 2, transform: "rotate(-3deg)" }}>
          {selo.toUpperCase()}
        </div>
      ) : null}

      {mood && !foto ? (
        <div style={{ position: "absolute", right: 60, top: 1210 }}>
          <Iva frame={0} fps={30} size={400} mood={mood} look={[-0.4, 0.2]} />
        </div>
      ) : null}

      <div style={{ position: "absolute", left: 80, top: 1600, display: "flex", alignItems: "center", gap: 16 }}>
        <svg width={70} height={38} viewBox="0 0 878 481"><path d={CLOUD_PATH} fill={k.logo} fillRule="evenodd" /><circle cx={810} cy={411} r={67} fill={C.ouro} /></svg>
        <div style={{ fontFamily: F.display, fontWeight: 500, fontSize: 30, letterSpacing: 8, color: k.logo }}>{marca.toUpperCase()}</div>
      </div>
    </AbsoluteFill>
  );
};
