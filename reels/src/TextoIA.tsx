import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { C } from "./theme";
import { Disc, Person, Shop, iso } from "./iso";
import { Karaoke, Line } from "./Captions";
import { Billboard, Bubble, CaptionVeil, Chip, EndCard, EndLayer, IvaActor, PhoneChat, Pill, Stage, SvgDefs, TopTitle, kf, sp } from "./common";

export const TEXTO_TIMES = { s1: 4.95, s2: 10.35, s3: 14.79, s4: 21.15, end: 23.6, total: 26.7 };
const T = TEXTO_TIMES;

const LINES: Line[] = [
  { from: 0.05, to: T.s1, text: "Seu cliente percebe quando o texto foi feito por *IA.* E isso afasta." },
  { from: T.s1, to: T.s2, text: "Sinal número um: *palavras* *que* *ninguém* *fala,* tipo potencialize e descubra." },
  { from: T.s2, to: T.s3, text: "Sinal dois: *elogio* *genérico,* que serve pra qualquer empresa." },
  { from: T.s3, to: T.s4, text: "A solução: cola três mensagens que você já mandou e pede pra IA escrever *do* *seu* *jeito.*" },
  { from: T.s4, to: T.end, text: "Salva pra usar na *próxima* *legenda.*" },
];

const SHOPS = [
  { x: -1.4, y: -2.2, s: 1.0, name: "BARBEARIA", a: "POTENCIALIZE SUA JORNADA" },
  { x: -5.4, y: 0.6, s: 0.75, name: "CAFÉ", a: "DESCUBRA O NOVO" },
  { x: 2.6, y: -4.6, s: 0.75, name: "ÓTICA", a: "TRANSFORME SUA VIDA" },
  { x: 2.2, y: 2.0, s: 0.75, name: "PET", a: "EXPERIÊNCIA ÚNICA" },
];
const GENERIC = "QUALIDADE E EXCELÊNCIA";
const REAL = "CORTE NA HORA, SEM FILA";

// troca de texto com o letreiro girando
const flipText = (t: number, at: number, a: string, b: string) => {
  const k = Math.min(1, Math.max(0, (t - at) / 0.45));
  return { text: k < 0.5 ? a : b, flip: Math.max(0.04, Math.abs(Math.cos(Math.PI * k))) };
};

export const TextoIA: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const OX = 540, OY = 900;
  const A = SHOPS[0];
  const [ax, ay] = iso(A.x + 1.1, A.y + 0.8, 1.6);
  const camX = kf(t, [[0, ax], [T.s1, ax], [T.s1 + 0.8, ax - 60], [T.s2, ax - 60], [T.s2 + 1.0, 0], [T.s3, 0], [T.s3 + 0.8, 230], [T.s4, 230], [T.s4 + 0.8, ax]]);
  const camY = kf(t, [[0, ay + 30], [T.s1, ay + 30], [T.s1 + 0.8, ay + 10], [T.s2, ay + 10], [T.s2 + 1.0, -20], [T.s3, -20], [T.s3 + 0.8, 60], [T.s4, 60], [T.s4 + 0.8, ay + 30]]);
  const zoom = kf(t, [[0, 1.2], [T.s1, 1.3], [T.s1 + 0.8, 1.2], [T.s2, 1.22], [T.s2 + 1.0, 0.86], [T.s3, 0.88], [T.s3 + 0.8, 0.8], [T.s4, 0.8], [T.s4 + 0.8, 1.25]]);
  const toScreen = (p: [number, number]) => [OX + (p[0] - camX) * zoom, OY + (p[1] - camY) * zoom] as [number, number];
  const endP = kf(t, [[T.end - 0.15, 0], [T.end + 0.25, 1]]);
  const won = kf(t, [[T.s4 + 0.5, 0], [T.s4 + 1.4, 1]]);

  const walkers = Array.from({ length: 14 }).map((_, i) => {
    // passam pela frente das lojas sem parar; no final, entram na barbearia
    const lane = A.y + 2.3 + (i % 3) * 0.5;
    let x = ((i * 1.7 + t * (0.55 + (i % 4) * 0.12)) % 13) - 6.5, y = lane + Math.sin(i) * 0.3;
    if (i >= 6) { const a = i * 2.2 + t * 0.09 * (i % 2 ? 1 : -1), r = 4.2 + (i % 3) * 0.8; x = Math.cos(a) * r; y = Math.sin(a) * r; }
    if (won > 0 && i < 8) { x += (A.x + 0.4 + (i % 4) * 0.4 - x) * won * 0.9; y += (A.y + 2.2 + Math.floor(i / 4) * 0.4 - y) * won * 0.9; }
    return { x, y };
  });
  const items: { d: number; el: React.ReactNode }[] = [];
  SHOPS.forEach((s, i) => {
    const w = 2.2 * s.s, d = 1.6 * s.s, h = 1.9 * s.s;
    let bb = flipText(t, T.s2 + 0.7 + 0.25 * i, s.a, GENERIC);
    if (i === 0 && t > T.s4) bb = flipText(t, T.s4 + 0.3, GENERIC, REAL);
    items.push({
      d: s.x + s.y + 3, el: (
        <g key={"s" + i}>
          <Shop x={s.x} y={s.y} s={s.s} name={s.name} lit={i === 0 ? 0.6 + 0.4 * won : 0.6} />
          <Billboard x={s.x} y={s.y + d} z={h} w={w} text={bb.text} tone={i === 0 && t > T.s4 + 0.52 ? "real" : "ia"} flip={bb.flip} />
        </g>
      ),
    });
  });
  walkers.forEach((p, i) => items.push({ d: p.x + p.y, el: <Person key={"w" + i} x={p.x} y={p.y} color={i === 2 ? C.azul : "#B5B0A4"} bob={Math.abs(Math.sin(t * 7 + i)) * 4} /> }));
  items.sort((a, b) => a.d - b.d);

  // sinal 1: palavras clichê riscadas
  const cliches = ["POTENCIALIZE", "DESCUBRA", "TRANSFORME SUA JORNADA"];
  const ivX = kf(t, [[0, 720], [T.s1, 720], [T.s1 + 0.8, 60], [T.s2, 60], [T.s2 + 1.0, 410], [T.s3, 410], [T.s3 + 0.8, 40], [T.s4, 40], [T.s4 + 0.8, 700]]);
  const ivY = kf(t, [[0, 470], [T.s1, 470], [T.s1 + 0.8, 470], [T.s2, 470], [T.s2 + 1.0, 330], [T.s3, 330], [T.s3 + 0.8, 1010], [T.s4, 1010], [T.s4 + 0.8, 450]]);
  const mood = t < T.s1 ? "surprise" : t < T.s2 ? "think" : t < T.s3 ? "think" : t > T.s4 + 1.0 ? "happy" : "idle";

  return (
    <Stage>
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0, opacity: 1 - endP }}>
        <SvgDefs />
        <g transform={`translate(${OX - camX * zoom},${OY - camY * zoom}) scale(${zoom})`}>
          <Disc cx={0} cy={0} r={7.4} thick={0.55}>
            <ellipse cx={0} cy={0} rx={1.2247 * 5.8 * 60} ry={0.7071 * 5.8 * 60} fill="none" stroke="#DCD6C8" strokeWidth={14} />
            <ellipse cx={0} cy={0} rx={1.2247 * 7.4 * 60} ry={0.7071 * 7.4 * 60} fill="none" stroke={C.ouro} strokeWidth={6} opacity={won} />
          </Disc>
          {items.map((i) => i.el)}
        </g>
      </svg>

      {/* gancho: alguém percebe */}
      {(() => { const p = toScreen(iso(walkers[2].x, walkers[2].y, 1.2)); return <Bubble x={p[0]} y={p[1]} p={sp(frame, fps, 1.3, 12) * kf(t, [[T.s1 - 0.3, 1], [T.s1, 0]])} text="ISSO AÍ É IA..." tone="bad" />; })()}
      {/* sinal 1 */}
      {cliches.map((c, i) => {
        const q = sp(frame, fps, T.s1 + 0.8 + 0.6 * i, 12) * kf(t, [[T.s2 - 0.3, 1], [T.s2, 0]]);
        const strike = kf(t, [[T.s1 + 1.3 + 0.6 * i, 0], [T.s1 + 1.7 + 0.6 * i, 1]]);
        return <Chip key={i} x={640} y={600 + i * 140} p={q} text={c} strike={strike} big />;
      })}
      {/* sinal 2: todo mundo igual */}
      {SHOPS.map((s, i) => {
        const p = toScreen(iso(s.x + 1.1 * s.s, s.y + 1.6 * s.s, 1.9 * s.s + 1.5));
        const q = sp(frame, fps, T.s2 + 1.6 + 0.2 * i, 12) * kf(t, [[T.s3 - 0.3, 1], [T.s3, 0]]);
        return <Chip key={"g" + i} x={p[0]} y={p[1] - 30} p={q} text="IGUAL" dot={C.vermelho} />;
      })}

      <PhoneChat frame={frame} fps={fps} t={t} t0={T.s3 + 0.2} contact="Assistente de IA" initials="IA" avatar={C.azul} label={["VOCÊ COLA", "3 MENSAGENS"]}
        p={sp(frame, fps, T.s3 + 0.2, 15) * kf(t, [[T.s4 - 0.1, 1], [T.s4 + 0.5, 0]])}
        msgs={[
          { me: true, text: "Bah, hoje o corte sai na hora 💈", at: 0.7, tag: "sua mensagem 1" },
          { me: true, text: "Tem horário livre à tarde, é só chamar 😉", at: 1.3, tag: "sua mensagem 2" },
          { me: true, text: "Sem fila até as 20h, só vir!", at: 1.9, tag: "sua mensagem 3" },
          { me: false, text: "Corte na hora e sem fila até as 20h. Chega mais! ✂️", at: 3.6, tag: "IA · do seu jeito" },
        ]} />

      <TopTitle small="SEU CLIENTE PERCEBE" big="QUANDO É IA" p={sp(frame, fps, 0.1) * kf(t, [[T.s1 - 0.25, 1], [T.s1 + 0.1, 0]])} bigSize={160} />
      <Pill a="SINAL 1 ·" b="PALAVRAS QUE NINGUÉM FALA" p={sp(frame, fps, T.s1) * kf(t, [[T.s2 - 0.3, 1], [T.s2, 0]])} />
      <Pill a="SINAL 2 ·" b="ELOGIO GENÉRICO" p={sp(frame, fps, T.s2) * kf(t, [[T.s3 - 0.3, 1], [T.s3, 0]])} />
      <Pill a="AGORA SIM ·" b="TEM A SUA CARA" p={sp(frame, fps, T.s4 + 0.5) * (1 - endP)} />

      <IvaActor frame={frame} fps={fps} x={ivX} y={ivY} size={t > T.s3 && t < T.s4 ? 220 : 250} mood={mood} talking={t < T.end && mood !== "happy"} enter={sp(frame, fps, 0.2, 12)}
        look={t > T.s3 && t < T.s4 ? [1, -0.4] : [0, 0.4]} opacity={1 - endP} />

      <CaptionVeil opacity={1 - endP} />
      <div style={{ opacity: 1 - endP }}><Karaoke frame={frame} fps={fps} lines={LINES} y={1330} /></div>
      <EndLayer p={endP}>
        <EndCard frame={frame - Math.round(T.end * fps)} fps={fps} product="CONTEÚDO" word="LEGENDA" sub="e eu te mando o prompt" foot={["Segue a Ciello", "pra mais dicas de IA."]} />
      </EndLayer>
    </Stage>
  );
};
