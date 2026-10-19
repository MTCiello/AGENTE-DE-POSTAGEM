import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { C, F } from "./theme";
import { Disc, Person, Shop, iso } from "./iso";
import { Karaoke, Line } from "./Captions";
import { Bubble, CaptionVeil, Chip, Coins, EndCard, EndLayer, IvaActor, Pill, Stage, SvgDefs, TopTitle, kf, sp } from "./common";

export const TESTE_TIMES = { s1: 4.27, s2: 10.26, s3: 14.67, s4: 19.97, end: 23.2, total: 26.9 };
const T = TESTE_TIMES;

const LINES: Line[] = [
  { from: 0.05, to: T.s1, text: "Antes de gastar *um* *real* no seu negócio, faz esse teste com IA." },
  { from: T.s1, to: T.s2, text: "Primeiro, pede pra ela agir como um *cliente* *desconfiado* e listar por que não compraria." },
  { from: T.s2, to: T.s3, text: "Depois, pede pra ela comparar com os *concorrentes* da sua cidade." },
  { from: T.s3, to: T.s4, text: "E por último, *faz* *a* *conta:* quanto você precisa vender por mês pra pagar tudo." },
  { from: T.s4, to: T.end, text: "Salva esse vídeo e *testa* *antes* *de* *abrir.*" },
];

const MAIN = { x: -1.3, y: -1.7 };
const RIVALS = [
  { x: -5.6, y: 0.9, name: "AROMA", tags: ["R$ 18 O COMBO", "DELIVERY PRÓPRIO"] },
  { x: 2.6, y: -5.0, name: "BISTRÔ", tags: ["BEM AVALIADO", "SEM DELIVERY"] },
  { x: 2.4, y: 2.4, name: "PADARIA", tags: ["ABERTA ATÉ 21H", "SEM SITE"] },
];
const DOUBTS = ["TÁ CARO", "NUNCA OUVI FALAR", "CADÊ AS AVALIAÇÕES?"];

export const TesteIdeia: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const OX = 540, OY = 900;

  // câmera
  const [mx, my] = iso(MAIN.x + 1.1, MAIN.y + 0.8, 1.0);
  const [fx, fy] = iso(MAIN.x + 1.1, MAIN.y + 2.6, 0.6);
  const camX = kf(t, [[0, mx], [T.s1, mx], [T.s1 + 0.9, fx], [T.s2, fx], [T.s2 + 1.0, 0], [T.s3, 0], [T.s3 + 0.8, 230], [T.s4, 230], [T.s4 + 0.8, mx]]);
  const camY = kf(t, [[0, my + 40], [T.s1, my + 40], [T.s1 + 0.9, fy - 40], [T.s2, fy - 40], [T.s2 + 1.0, 20], [T.s3, 20], [T.s3 + 0.8, 60], [T.s4, 60], [T.s4 + 0.8, my + 60]]);
  const zoom = kf(t, [[0, 1.15], [T.s1, 1.28], [T.s1 + 0.9, 1.3], [T.s2, 1.34], [T.s2 + 1.0, 0.82], [T.s3, 0.84], [T.s3 + 0.8, 0.8], [T.s4, 0.8], [T.s4 + 0.8, 1.15]]);
  const toScreen = (p: [number, number]) => [OX + (p[0] - camX) * zoom, OY + (p[1] - camY) * zoom] as [number, number];

  const opened = kf(t, [[T.s4 + 0.4, 0], [T.s4 + 1.2, 1]]);
  const contaP = kf(t, [[T.s3 + 1.4, 0], [T.s3 + 2.6, 1]]);
  const endP = kf(t, [[T.end - 0.15, 0], [T.end + 0.25, 1]]);

  // pessoas: três desconfiadas na frente da loja (teste 1) + passantes
  const front = [0, 1, 2].map((i) => ({ x: MAIN.x + 0.2 + i * 0.75, y: MAIN.y + 2.5 + (i % 2) * 0.35 }));
  const walkers = Array.from({ length: 12 }).map((_, i) => {
    const r = 3.6 + (i % 4) * 0.8, a = i * 2.4 + t * (0.07 + (i % 3) * 0.025) * (i % 2 ? 1 : -1);
    let x = Math.cos(a) * r, y = Math.sin(a) * r;
    if (opened > 0 && i % 2 === 0) { x += (MAIN.x + 0.5 + (i % 5) * 0.35 - x) * opened * 0.9; y += (MAIN.y + 2.3 + (i % 3) * 0.3 - y) * opened * 0.9; }
    return { x, y };
  });
  const items: { d: number; el: React.ReactNode }[] = [];
  items.push({ d: MAIN.x + MAIN.y + 3, el: <Shop key="main" x={MAIN.x} y={MAIN.y} s={1} name={opened > 0.5 ? "ABERTO" : "EM BREVE"} closed={opened < 0.5} lit={opened} /> });
  RIVALS.forEach((r, i) => items.push({ d: r.x + r.y + 2.3, el: <Shop key={"r" + i} x={r.x} y={r.y} s={0.75} name={r.name} lit={0.6} /> }));
  items.push({ d: 1.6 + 0.5, el: <Coins key="coins" x={1.9} y={-0.3} n={2 + 9 * contaP} r={0.62} /> });
  front.forEach((p, i) => items.push({ d: p.x + p.y, el: <Person key={"f" + i} x={p.x} y={p.y} color={i === 1 ? C.azul : "#B5B0A4"} bob={0} /> }));
  walkers.forEach((p, i) => items.push({ d: p.x + p.y, el: <Person key={"w" + i} x={p.x} y={p.y} color="#BDB8AC" bob={Math.abs(Math.sin(t * 6 + i)) * 4} /> }));
  items.sort((a, b) => a.d - b.d);

  // I.V.A.
  const ivX = kf(t, [[0, 700], [T.s1, 700], [T.s1 + 0.9, 60], [T.s2, 60], [T.s2 + 1.0, 400], [T.s3, 400], [T.s3 + 0.8, 40], [T.s4, 40], [T.s4 + 0.8, 690]]);
  const ivY = kf(t, [[0, 520], [T.s1, 520], [T.s1 + 0.9, 430], [T.s2, 430], [T.s2 + 1.0, 330], [T.s3, 330], [T.s3 + 0.8, 1010], [T.s4, 1010], [T.s4 + 0.8, 470]]);
  const mood = t > T.s1 && t < T.s2 ? "think" : t > T.s4 + 0.8 ? "happy" : t > T.s3 + 2.6 && t < T.s4 ? "surprise" : "idle";
  const dotAway = t > T.s3 + 2.4 && t < T.s4 - 0.2 ? kf(t, [[T.s3 + 2.4, 0], [T.s3 + 2.8, 1]]) : 0;

  return (
    <Stage>
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0, opacity: 1 - endP }}>
        <SvgDefs />
        <g transform={`translate(${OX - camX * zoom},${OY - camY * zoom}) scale(${zoom})`}>
          <Disc cx={0} cy={0} r={7.4} thick={0.55}>
            <ellipse cx={0} cy={0} rx={1.2247 * 5.8 * 60} ry={0.7071 * 5.8 * 60} fill="none" stroke="#DCD6C8" strokeWidth={14} />
            <ellipse cx={0} cy={0} rx={1.2247 * 7.4 * 60} ry={0.7071 * 7.4 * 60} fill="none" stroke={C.ouro} strokeWidth={6} opacity={opened} />
          </Disc>
          {items.map((i) => i.el)}
        </g>
      </svg>

      {/* teste 1: balões das dúvidas */}
      {front.map((p, i) => {
        const s = toScreen(iso(p.x, p.y, 1.2));
        const q = sp(frame, fps, T.s1 + 1.3 + 0.9 * i, 12) * kf(t, [[T.s2 - 0.3, 1], [T.s2, 0]]);
        return <Bubble key={i} x={s[0]} y={s[1] - 10 - (i % 2) * 70} p={q} text={DOUBTS[i]} tone="bad" />;
      })}
      {/* teste 2: o que cada concorrente tem */}
      {RIVALS.map((r, k) => {
        const s = toScreen(iso(r.x + 0.8, r.y + 0.6, 2.4));
        return r.tags.map((tag, j) => {
          const q = sp(frame, fps, T.s2 + 1.0 + 0.55 * k + 0.2 * j, 13) * kf(t, [[T.s3 - 0.3, 1], [T.s3, 0]]);
          const bad = tag.startsWith("SEM");
          return <Chip key={k + "-" + j} x={s[0]} y={s[1] - 80 + j * 66} p={q} text={tag} dot={bad ? C.vermelho : C.verde} />;
        });
      })}

      {/* teste 3: a conta */}
      <Conta t={t} frame={frame} fps={fps} />

      {/* topo */}
      <TopTitle small="TESTE SUA IDEIA ANTES DE GASTAR" big="UM REAL" p={sp(frame, fps, 0.1) * kf(t, [[T.s1 - 0.25, 1], [T.s1 + 0.1, 0]])} bigSize={170} />
      <Pill a="TESTE 1 ·" b="O CLIENTE DESCONFIADO" p={sp(frame, fps, T.s1) * kf(t, [[T.s2 - 0.3, 1], [T.s2, 0]])} />
      <Pill a="TESTE 2 ·" b="A CONCORRÊNCIA" p={sp(frame, fps, T.s2) * kf(t, [[T.s3 - 0.3, 1], [T.s3, 0]])} />
      <Pill a="TESTE 3 ·" b="A CONTA" p={sp(frame, fps, T.s3) * kf(t, [[T.s4 - 0.3, 1], [T.s4, 0]])} />
      <Pill a="AGORA SIM ·" b="PODE ABRIR" p={sp(frame, fps, T.s4 + 0.5) * (1 - endP)} />

      <IvaActor frame={frame} fps={fps} x={ivX} y={ivY} size={t > T.s3 && t < T.s4 ? 220 : 250} mood={mood} talking={t < T.end && mood !== "happy"} enter={sp(frame, fps, 0.2, 12)}
        look={t > T.s1 && t < T.s2 ? [1, 0.5] : t > T.s3 && t < T.s4 ? [1, -0.4] : [0, 0.3]} dot={{ x: 760, y: 760, away: dotAway }} opacity={1 - endP} />

      <CaptionVeil opacity={1 - endP} />
      <div style={{ opacity: 1 - endP }}><Karaoke frame={frame} fps={fps} lines={LINES} y={1330} /></div>
      <EndLayer p={endP}>
        <EndCard frame={frame - Math.round(T.end * fps)} fps={fps} product="CONSULTORIA" word="TESTE" sub="e eu te mando os 3 prompts" foot={["Precisa de site ou automação?", "Chama a Ciello."]} />
      </EndLayer>
    </Stage>
  );
};

const Conta: React.FC<{ t: number; frame: number; fps: number }> = ({ t, frame, fps }) => {
  const p = sp(frame, fps, T.s3 + 0.5, 15) * kf(t, [[T.s4 - 0.1, 1], [T.s4 + 0.4, 0]]);
  if (p <= 0.01) return null;
  const row = (k: number) => sp(frame, fps, T.s3 + 0.9 + 0.35 * k, 14);
  const n = Math.round(kf(t, [[T.s3 + 1.8, 0], [T.s3 + 2.8, 120]]));
  const R: React.FC<{ k: number; a: string; b: string; strong?: boolean }> = ({ k, a, b, strong }) => (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", opacity: row(k), transform: `translateX(${(1 - row(k)) * 30}px)`, padding: "14px 0", borderBottom: "2px dashed #DDD6C8" }}>
      <span style={{ fontFamily: F.ui, fontSize: 30, color: "#5E5A51" }}>{a}</span>
      <span style={{ fontFamily: F.display, fontWeight: strong ? 700 : 600, fontSize: strong ? 44 : 38, color: C.carvao }}>{b}</span>
    </div>
  );
  return (
    <div style={{ position: "absolute", left: 470 + (1 - p) * 520, top: 300, width: 560, background: C.papel, borderRadius: 30, padding: "34px 40px 40px", boxShadow: "0 40px 80px rgba(40,30,10,0.28)", transform: `rotate(${(1 - p) * 5 + 1.2}deg)` }}>
      <div style={{ fontFamily: F.display, fontWeight: 600, fontSize: 28, letterSpacing: 8, color: "#7C776B", marginBottom: 8 }}>A IA FAZ <span style={{ color: C.carvao }}>A CONTA</span></div>
      <R k={0} a="Custos do mês" b="R$ 3.000" />
      <R k={1} a="Ticket médio" b="÷ R$ 25" />
      <div style={{ marginTop: 26, opacity: row(2) }}>
        <div style={{ fontFamily: F.ui, fontSize: 28, color: "#5E5A51" }}>Você precisa vender</div>
        <div style={{ fontFamily: F.display, fontWeight: 700, fontSize: 150, lineHeight: 1, color: C.carvao }}>
          {n}<span style={{ fontSize: 46, color: "#7C776B", marginLeft: 14 }}>por mês</span>
        </div>
        <div style={{ height: 12, background: C.ouro, width: `${kf(t, [[T.s3 + 2.6, 0], [T.s3 + 3.0, 100]])}%`, borderRadius: 3, marginTop: -6 }} />
      </div>
      <div style={{ marginTop: 26, display: "flex", gap: 14, flexWrap: "wrap" }}>
        <Pill2 p={row(6)} text="≈ 5 POR DIA ÚTIL" />
        <Pill2 p={row(7)} text="META COM FOLGA: 150" gold />
      </div>
    </div>
  );
};
const Pill2: React.FC<{ p: number; text: string; gold?: boolean }> = ({ p, text, gold }) => (
  <div style={{ opacity: p, transform: `scale(${0.7 + 0.3 * p})`, background: gold ? C.ouro : C.carvao, color: gold ? C.carvao : C.branco, borderRadius: 30, padding: "12px 24px", fontFamily: F.display, fontWeight: 600, fontSize: 28, letterSpacing: 1 }}>{text}</div>
);
