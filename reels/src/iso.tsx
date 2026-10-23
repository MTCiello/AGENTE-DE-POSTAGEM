import React from "react";
import { C, F } from "./theme";

// Projeção isométrica: mundo (x, y no chão, z para cima) -> tela
export const U = 60; // tamanho da unidade em px (antes da câmera)
export const iso = (x: number, y: number, z = 0): [number, number] => [
  (x - y) * 0.866 * U,
  (x + y) * 0.5 * U - z * U,
];
const pts = (p: [number, number][]) => p.map((q) => q.join(",")).join(" ");

// matriz SVG para desenhar "colado" na face frontal-esquerda (plano x/z, voltada para +y)
export const faceLeft = (x: number, y: number, z: number) => {
  const [ox, oy] = iso(x, y, z);
  return `matrix(${0.866 * U},${0.5 * U},0,${U},${ox},${oy})`;
};
// face frontal-direita (plano y/z, voltada para +x), lida da esquerda para a direita
export const faceRight = (x: number, y: number, z: number) => {
  const [ox, oy] = iso(x, y, z);
  return `matrix(${0.866 * U},${-0.5 * U},0,${U},${ox},${oy})`;
};

export const Box: React.FC<{
  x: number; y: number; w: number; d: number; h: number;
  top?: string; left?: string; right?: string; stroke?: string;
  children?: React.ReactNode; rightChildren?: React.ReactNode;
}> = ({ x, y, w, d, h, top = "#2c2b29", left = "#1d1c1b", right = "#121211", stroke, children, rightChildren }) => (
  <g>
    <polygon points={pts([iso(x, y, h), iso(x + w, y, h), iso(x + w, y + d, h), iso(x, y + d, h)])} fill={top} stroke={stroke} />
    <polygon points={pts([iso(x, y + d, 0), iso(x + w, y + d, 0), iso(x + w, y + d, h), iso(x, y + d, h)])} fill={left} stroke={stroke} />
    <polygon points={pts([iso(x + w, y, 0), iso(x + w, y + d, 0), iso(x + w, y + d, h), iso(x + w, y, h)])} fill={right} stroke={stroke} />
    {children ? <g transform={faceLeft(x, y + d, h)}>{children}</g> : null}
    {rightChildren ? <g transform={faceRight(x + w, y + d, h)}>{rightChildren}</g> : null}
  </g>
);

// disco (tabuleiro) — elipse isométrica com espessura
export const Disc: React.FC<{ cx: number; cy: number; r: number; thick?: number; fill?: string; side?: string; children?: React.ReactNode }> = ({
  cx, cy, r, thick = 0.5, fill = C.papel, side = "#CFC9BA", children,
}) => {
  const [sx, sy] = iso(cx, cy, 0);
  const rx = 1.2247 * r * U, ry = 0.7071 * r * U, t = thick * U;
  return (
    <g>
      <ellipse cx={sx} cy={sy + t + 26} rx={rx * 1.02} ry={ry * 1.02} fill="rgba(60,50,30,0.18)" filter="url(#blur18)" />
      <path d={`M ${sx - rx} ${sy} L ${sx - rx} ${sy + t} A ${rx} ${ry} 0 0 0 ${sx + rx} ${sy + t} L ${sx + rx} ${sy} Z`} fill={side} />
      <ellipse cx={sx} cy={sy} rx={rx} ry={ry} fill={fill} />
      {children}
    </g>
  );
};

// loja isométrica (caixa carvão com toldo ouro/creme, vitrine e letreiro)
export const Shop: React.FC<{ x: number; y: number; s?: number; name?: string; lit?: number; closed?: boolean }> = ({
  x, y, s = 1, name = "LOJA", lit = 1, closed = false,
}) => {
  const w = 2.2 * s, d = 1.6 * s, h = 1.9 * s;
  return (
    <g>
      <ellipse cx={iso(x + w / 2, y + d / 2)[0]} cy={iso(x + w / 2, y + d / 2)[1] + 6} rx={w * U * 0.95} ry={d * U * 0.55} fill="rgba(60,50,30,0.16)" filter="url(#blur8)" />
      <Box x={x} y={y} w={w} d={d} h={h}>
        {/* letreiro */}
        <rect x={0.35 * s} y={0.22 * s} width={1.5 * s} height={0.34 * s} fill={C.carvao} />
        <text x={1.1 * s} y={0.48 * s} fontSize={0.26 * s} fontFamily={F.display} fontWeight={600} fill={C.ouro} textAnchor="middle" letterSpacing={0.04 * s}>{name}</text>
        {/* toldo */}
        {Array.from({ length: 6 }).map((_, i) => (
          <polygon key={i} points={`${0.25 * s + i * 0.29 * s},${0.72 * s} ${0.25 * s + (i + 1) * 0.29 * s},${0.72 * s} ${0.25 * s + (i + 1) * 0.29 * s - 0.03 * s},${0.95 * s} ${0.25 * s + i * 0.29 * s + 0.03 * s},${0.95 * s}`} fill={i % 2 ? C.papel : C.ouro} />
        ))}
        {/* vitrine */}
        <rect x={0.3 * s} y={0.98 * s} width={1.6 * s} height={0.78 * s} fill={closed ? "#8f8a80" : `rgba(246, 226, 160, ${0.35 + 0.65 * lit})`} />
        {closed && Array.from({ length: 6 }).map((_, i) => <rect key={i} x={0.3 * s} y={(1.02 + i * 0.12) * s} width={1.6 * s} height={0.05 * s} fill="#6f6b63" />)}
      </Box>
    </g>
  );
};

// pessoinha (cilindro + cabeça), como no reel da escala 6x1
export const Person: React.FC<{ x: number; y: number; color?: string; s?: number; bob?: number }> = ({ x, y, color = "#B9B4A8", s = 1, bob = 0 }) => {
  const [px, py] = iso(x, y, 0);
  const bw = 0.22 * U * s, bh = 0.62 * U * s;
  return (
    <g transform={`translate(${px},${py - bob})`}>
      <ellipse cx={0} cy={bob} rx={bw * 0.9} ry={bw * 0.42} fill="rgba(40,35,25,0.22)" />
      <rect x={-bw / 2} y={-bh} width={bw} height={bh} rx={bw / 2} fill={color} />
      <rect x={-bw / 2} y={-bh} width={bw * 0.42} height={bh} rx={bw / 4} fill="rgba(255,255,255,0.18)" />
      <circle cx={0} cy={-bh - bw * 0.62} r={bw * 0.55} fill={color} />
    </g>
  );
};

// pino de localização dourado flutuando
export const Pin: React.FC<{ x: number; y: number; z: number; p: number; label?: string }> = ({ x, y, z, p, label }) => {
  if (p <= 0) return null;
  const [px, py] = iso(x, y, z);
  const s = Math.min(1.15, p);
  return (
    <g transform={`translate(${px},${py}) scale(${s})`} opacity={Math.min(1, p * 2)}>
      <path d="M0,0 C-26,-30 -30,-46 -30,-58 A30,30 0 1 1 30,-58 C30,-46 26,-30 0,0 Z" fill={C.ouro} stroke={C.carvao} strokeWidth={3} />
      <circle cx={0} cy={-58} r={11} fill={C.carvao} />
      {label ? (
        <g transform="translate(0,-112)">
          <rect x={-label.length * 9.5 - 18} y={-26} width={label.length * 19 + 36} height={46} rx={23} fill={C.carvao} />
          <text x={0} y={7} textAnchor="middle" fontFamily={F.display} fontWeight={600} fontSize={24} fill={C.branco} letterSpacing={1}>{label}</text>
        </g>
      ) : null}
    </g>
  );
};
