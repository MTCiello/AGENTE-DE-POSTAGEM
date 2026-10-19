import React from "react";
import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { C, F } from "./theme";
import { Disc, Person, Pin, Shop, iso } from "./iso";
import { Iva, Pontinho } from "./Iva";
import { Karaoke, Line } from "./Captions";
import { CLOUD_PATH } from "./cloudPath";

// ---- tempos (segundos) vindos da narração ----
export const VENDEDOR_TIMES = { s1: 2.38, s2: 7.36, s3: 11.64, s4: 16.9, end: 20.2, total: 24.3 };
const T = VENDEDOR_TIMES;

const LINES: Line[] = [
  { from: 0.05, to: T.s1, text: "Imagina um vendedor que *não* *dorme.*" },
  { from: T.s1, to: T.s2, text: "Você diz o cliente que quer, e a IA *encontra* *as* *empresas* da sua região." },
  { from: T.s2, to: T.s3, text: "Depois ela *pesquisa* *cada* *uma:* o que vende, o que tá faltando." },
  { from: T.s3, to: T.s4, text: "E escreve uma *mensagem* *personalizada* pra cada dono. Você só revisa e manda." },
  { from: T.s4, to: T.end, text: "Isso já dá pra montar hoje com o *Claude.*" },
];

const SHOPS = [
  { x: -3.6, y: -3.2, name: "CAFÉ" },
  { x: 0.4, y: -4.9, name: "BARBEARIA", target: 0 },
  { x: 3.3, y: -1.6, name: "PET SHOP" },
  { x: -5.0, y: 0.6, name: "BARBEARIA", target: 1 },
  { x: -1.0, y: 2.6, name: "ÓTICA" },
  { x: 2.4, y: 2.9, name: "BARBEARIA", target: 2 },
];
const TAGS = [
  ["SEM SITE", "4,8 ★ GOOGLE"],
  ["SEM SITE", "INSTA PARADO"],
  ["SEM AGENDAMENTO"],
];

const ease = Easing.bezier(0.65, 0, 0.35, 1);
const kf = (t: number, keys: [number, number][]) =>
  interpolate(t, keys.map((k) => k[0]), keys.map((k) => k[1]), { easing: ease, extrapolateLeft: "clamp", extrapolateRight: "clamp" });

// alvo do mundo: centro do tabuleiro em (0,0); câmera = ponto do mundo no centro + zoom
const SS = 0.75; // escala das lojas
const shopCenter = (i: number) => iso(SHOPS[i].x + 1.1 * SS, SHOPS[i].y + 0.8 * SS, 1.0);

export const VendedorIA: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, width } = useVideoConfig();
  const t = frame / fps;

  // ---------------- câmera ----------------
  const [ax, ay] = shopCenter(1), [bx, by] = shopCenter(3), [cx2, cy2] = shopCenter(5);
  const camX = kf(t, [[0, 0], [T.s1, 0], [T.s1 + 1, 0], [T.s2, ax], [T.s2 + 1.4, bx], [T.s2 + 2.9, cx2], [T.s3, 140], [T.s4, 140], [T.s4 + 0.8, 0]]);
  const camY = kf(t, [[0, 40], [T.s1, 40], [T.s1 + 1, 0], [T.s2, ay], [T.s2 + 1.4, by], [T.s2 + 2.9, cy2], [T.s3, 60], [T.s4, 60], [T.s4 + 0.8, 30]]);
  const zoom = kf(t, [[0, 0.92], [T.s1, 1.0], [T.s1 + 1, 1.08], [T.s2 - 0.4, 1.12], [T.s2 + 0.6, 1.55], [T.s3 - 0.3, 1.55], [T.s3 + 0.6, 0.86], [T.s4, 0.86], [T.s4 + 0.8, 0.98]]);
  const OX = width / 2, OY = 900;
  const toScreen = (p: [number, number]) => [OX + (p[0] - camX) * zoom, OY + (p[1] - camY) * zoom] as const;

  // pinos (passo 1)
  const pinP = (k: number) => spring({ frame: frame - Math.round((T.s1 + 1.2 + 0.45 * k) * fps), fps, config: { damping: 11, mass: 0.7 } });
  // tags (passo 2): uma loja por vez
  const tagP = (k: number, j: number) => spring({ frame: frame - Math.round((T.s2 + 0.7 + 1.4 * k + 0.25 * j) * fps), fps, config: { damping: 13 } });

  // ---------------- I.V.A. ----------------
  const ivaHome = (p: [number, number], dx = -40, dy = -330) => [p[0] + dx, p[1] + dy] as [number, number];
  const iv0 = [700, 560], ivA = ivaHome(toScreen(shopCenter(1)) as any), ivB = ivaHome(toScreen(shopCenter(3)) as any), ivC = ivaHome(toScreen(shopCenter(5)) as any);
  const ivX = kf(t, [[0, iv0[0]], [T.s1 + 1, iv0[0]], [T.s1 + 1.2, 640], [T.s2, ivA[0]], [T.s2 + 1.4, ivB[0]], [T.s2 + 2.9, ivC[0]], [T.s3 - 0.1, ivC[0]], [T.s3 + 0.7, 70], [T.s4, 70], [T.s4 + 0.8, 380]]);
  const ivY = kf(t, [[0, iv0[1]], [T.s1 + 1, iv0[1]], [T.s1 + 1.2, 470], [T.s2, ivA[1]], [T.s2 + 1.4, ivB[1]], [T.s2 + 2.9, ivC[1]], [T.s3 - 0.1, ivC[1]], [T.s3 + 0.7, 1060], [T.s4, 1060], [T.s4 + 0.8, 520]]);
  const ivIn = spring({ frame: frame - 6, fps, config: { damping: 12 } });
  const bob = Math.sin(t * 2.4) * 10;
  const ivSize = t > T.s3 && t < T.s4 ? 230 : 270;
  const mood = t < T.s1 ? "idle" : t < T.s2 ? "idle" : t < T.s3 ? "think" : t > T.s4 + 0.6 ? "happy" : "idle";
  // pontinho: sai do lugar dele no logo e vai até o que a I.V.A. está mostrando
  const dotHome: [number, number] = [ivX + ivSize * (810 / 878), ivY + bob + ivSize * (481 / 878) * (411 / 481)];
  let dotTarget = dotHome;
  if (t > T.s1 + 1.0 && t < T.s2) {
    const k = Math.min(2, Math.floor((t - T.s1 - 1.2) / 0.45));
    if (k >= 0) { const s = toScreen(iso(SHOPS[[1, 3, 5][k]].x + 1.1 * SS, SHOPS[[1, 3, 5][k]].y + 0.8 * SS, 2.1)); dotTarget = [s[0], s[1] - 130 * zoom]; }
  }
  const dotX = dotHome[0] + (dotTarget[0] - dotHome[0]) * (t > T.s1 + 1.0 && t < T.s2 ? kf(t, [[T.s1 + 1.0, 0], [T.s1 + 1.3, 1]]) : 0);
  const dotY = dotHome[1] + (dotTarget[1] - dotHome[1]) * (t > T.s1 + 1.0 && t < T.s2 ? kf(t, [[T.s1 + 1.0, 0], [T.s1 + 1.3, 1]]) : 0);

  // ---------------- títulos (topo) ----------------
  const titleIn = spring({ frame: frame - 3, fps, config: { damping: 14 } });
  const titleOut = kf(t, [[T.s1 - 0.25, 1], [T.s1 + 0.1, 0]]);
  const pillP = spring({ frame: frame - Math.round(T.s1 * fps), fps, config: { damping: 14 } });
  const query = "barbearias em Chapecó";
  const typed = query.slice(0, Math.round(kf(t, [[T.s1 + 0.3, 0], [T.s1 + 1.1, query.length]])));
  const pillOut = kf(t, [[T.s2 - 0.3, 1], [T.s2, 0]]);
  const l2 = spring({ frame: frame - Math.round(T.s2 * fps), fps, config: { damping: 14 } }) * kf(t, [[T.s3 - 0.3, 1], [T.s3, 0]]);

  // ---------------- celular (passo 3) ----------------
  const phoneP = spring({ frame: frame - Math.round((T.s3 + 0.2) * fps), fps, config: { damping: 15, mass: 0.9 } }) * kf(t, [[T.s4 - 0.1, 1], [T.s4 + 0.5, 0]]);
  const msgs = [
    { me: true, text: "Oi, Rafa! Vi que a Barbearia do Centro tem 4,8 no Google, mas ainda não tem agendamento online.", at: 0.9 },
    { me: true, text: "Posso te mostrar como ficaria? Leva 2 minutos.", at: 2.0 },
    { me: false, text: "Opa, pode mandar! 👊", at: 3.3 },
  ];

  // ---------------- final (escuro) ----------------
  const endP = kf(t, [[T.end - 0.15, 0], [T.end + 0.25, 1]]);
  const worldLit = kf(t, [[T.s4 + 0.3, 0], [T.s4 + 1.5, 1]]);
  const dim = 0;

  // pessoas andando
  const people = Array.from({ length: 18 }).map((_, i) => {
    const r = 1.6 + (i % 6) * 0.75, a = i * 2.1 + t * (0.08 + (i % 3) * 0.03) * (i % 2 ? 1 : -1);
    let x = Math.cos(a) * r, y = Math.sin(a) * r;
    // no final, metade caminha até as lojas-alvo
    if (worldLit > 0 && i % 2 === 0) {
      const s = SHOPS[[1, 3, 5][i % 3]];
      x = x + (s.x + 0.8 + (i % 4) * 0.25 - x) * worldLit * 0.85; y = y + (s.y + 1.7 - y) * worldLit * 0.85;
    }
    return { x, y, c: i % 7 === 3 ? C.azul : "#B5B0A4", bob: Math.abs(Math.sin(t * 6 + i)) * 4 };
  });
  const drawables: { depth: number; el: React.ReactNode }[] = [];
  SHOPS.forEach((s, i) => drawables.push({ depth: s.x + s.y + 3, el: <Shop key={"s" + i} x={s.x} y={s.y} s={SS} name={s.name} lit={t < T.s1 ? 1 : 0.5 + 0.5 * worldLit} /> }));
  people.forEach((p, i) => drawables.push({ depth: p.x + p.y, el: <Person key={"p" + i} x={p.x} y={p.y} color={p.c} bob={p.bob} /> }));
  drawables.sort((a, b) => a.depth - b.depth);

  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 42%, ${C.cremeClaro} 0%, ${C.creme} 55%, ${C.cremeEscuro} 100%)`, overflow: "hidden" }}>
      {/* ---------- mundo isométrico ---------- */}
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0, opacity: 1 - endP }}>
        <defs>
          <filter id="blur18" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="18" /></filter>
          <filter id="blur8" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="8" /></filter>
        </defs>
        <g transform={`translate(${OX - camX * zoom},${OY - camY * zoom}) scale(${zoom})`}>
          <Disc cx={0} cy={0} r={7.2} thick={0.55}>
            {/* anel central e ruas */}
            <ellipse cx={0} cy={0} rx={1.2247 * 1.4 * 60} ry={0.7071 * 1.4 * 60} fill="#D9D3C4" />
            <ellipse cx={0} cy={0} rx={1.2247 * 5.6 * 60} ry={0.7071 * 5.6 * 60} fill="none" stroke="#DCD6C8" strokeWidth={14} />
            <ellipse cx={0} cy={0} rx={1.2247 * 7.2 * 60} ry={0.7071 * 7.2 * 60} fill="none" stroke={C.ouro} strokeWidth={6} opacity={worldLit} />
          </Disc>
          {drawables.map((d) => d.el)}
          {[1, 3, 5].map((si, k) => (
            <Pin key={k} x={SHOPS[si].x + 1.1 * SS} y={SHOPS[si].y + 0.8 * SS} z={2.1} p={pinP(k) * (t < T.s3 ? 1 : kf(t, [[T.s3, 1], [T.s3 + 0.4, 0]])) + (t > T.s4 ? worldLit : 0)} label={t > T.s4 ? "✓" : undefined} />
          ))}
        </g>
      </svg>
      <AbsoluteFill style={{ background: C.carvao, opacity: dim }} />

      {/* ---------- tags de pesquisa (passo 2) ---------- */}
      {[1, 3, 5].map((si, k) => {
        const p0 = toScreen(iso(SHOPS[si].x + 2.2 * SS, SHOPS[si].y + 0.2, 1.9));
        const vis = t > T.s2 && t < T.s3 ? 1 : 0;
        return TAGS[k].map((tag, j) => {
          const p = tagP(k, j) * vis;
          if (p <= 0.01) return null;
          const bad = tag.startsWith("SEM") || tag.includes("PARADO");
          return (
            <div key={k + "-" + j} style={{
              position: "absolute", left: p0[0] + 30, top: p0[1] - 60 + j * 74, transform: `scale(${p}) translateX(${(1 - p) * -40}px)`, transformOrigin: "left center",
              background: C.papel, borderRadius: 40, padding: "12px 26px 12px 18px", display: "flex", alignItems: "center", gap: 12,
              boxShadow: "0 14px 30px rgba(60,45,20,0.22)", fontFamily: F.display, fontWeight: 600, fontSize: 30, letterSpacing: 1, color: C.carvao,
            }}>
              <span style={{ width: 22, height: 22, borderRadius: 11, background: bad ? C.vermelho : C.verde, display: "inline-block" }} />
              {tag}
            </div>
          );
        });
      })}

      {/* ---------- título do gancho ---------- */}
      <div style={{ position: "absolute", top: 150, width: "100%", textAlign: "center", opacity: titleIn * titleOut * (1 - endP), transform: `translateY(${(1 - titleIn) * -30}px)` }}>
        <div style={{ fontFamily: F.display, fontWeight: 600, fontSize: 40, letterSpacing: 12, color: "#4A4740" }}>UM VENDEDOR QUE</div>
        <div style={{ fontFamily: F.display, fontWeight: 700, fontSize: 150, lineHeight: 1.0, color: C.carvao, letterSpacing: -1 }}>NÃO DORME</div>
      </div>
      {/* pílula de horário (gancho) */}
      <div style={{ position: "absolute", top: 420, left: 0, right: 0, display: "flex", justifyContent: "center", opacity: titleIn * titleOut }}>
        <div style={{ background: C.carvao, color: C.branco, borderRadius: 40, padding: "12px 30px", fontFamily: F.display, fontWeight: 500, fontSize: 34, letterSpacing: 2 }}>
          SEGUNDA · <span style={{ color: C.ouro }}>03:12</span>
        </div>
      </div>

      {/* ---------- busca (passo 1) ---------- */}
      <div style={{ position: "absolute", top: 210, left: 0, right: 0, display: "flex", justifyContent: "center", opacity: pillP * pillOut, transform: `translateY(${(1 - pillP) * -40}px)` }}>
        <div style={{ background: C.carvao, color: C.branco, borderRadius: 50, padding: "20px 40px", minWidth: 640, display: "flex", alignItems: "center", gap: 18, fontFamily: F.ui, fontSize: 38, boxShadow: "0 18px 40px rgba(40,30,10,0.25)" }}>
          <svg width={34} height={34} viewBox="0 0 24 24"><circle cx="10" cy="10" r="7" stroke={C.ouro} strokeWidth="2.6" fill="none" /><line x1="15" y1="15" x2="21" y2="21" stroke={C.ouro} strokeWidth="2.6" strokeLinecap="round" /></svg>
          <span>{typed}<span style={{ opacity: Math.floor(t * 3) % 2 ? 0 : 1, color: C.ouro }}>|</span></span>
        </div>
      </div>
      <div style={{ position: "absolute", top: 330, width: "100%", textAlign: "center", opacity: pillP * pillOut, fontFamily: F.display, fontWeight: 600, fontSize: 34, letterSpacing: 8, color: "#4A4740" }}>
        3 SEM SITE ENCONTRADAS
      </div>
      {/* rótulo passo 2 */}
      <div style={{ position: "absolute", top: 200, left: 0, right: 0, display: "flex", justifyContent: "center", opacity: l2, transform: `translateY(${(1 - l2) * -30}px)` }}>
        <div style={{ background: C.carvao, color: C.branco, borderRadius: 40, padding: "14px 34px", fontFamily: F.display, fontWeight: 500, fontSize: 34, letterSpacing: 3 }}>
          ANALISANDO <span style={{ color: C.ouro }}>3 EMPRESAS</span>
        </div>
      </div>

      {/* ---------- celular com a conversa (passo 3) ---------- */}
      {phoneP > 0.01 ? (
        <div style={{ position: "absolute", left: 300 + (1 - phoneP) * 600, top: 230, width: 680, height: 1010, transform: `rotate(${(1 - phoneP) * 6}deg)` }}>
          <div style={{ position: "absolute", top: -64, left: 10, fontFamily: F.display, fontWeight: 600, fontSize: 32, letterSpacing: 8, color: "#4A4740" }}>
            A IA <span style={{ color: C.carvao }}>ESCREVE</span>
          </div>
          <div style={{ position: "absolute", inset: 0, borderRadius: 70, background: C.carvao, padding: 16, boxShadow: "0 40px 80px rgba(40,30,10,0.35)" }}>
            <div style={{ position: "absolute", inset: 16, borderRadius: 56, background: "#ECE7DC", overflow: "hidden" }}>
              <div style={{ background: C.papel, padding: "70px 32px 24px", display: "flex", alignItems: "center", gap: 18, borderBottom: "2px solid #DDD6C8" }}>
                <div style={{ width: 70, height: 70, borderRadius: 35, background: C.verde, color: "#fff", fontFamily: F.ui, fontWeight: 700, fontSize: 28, display: "flex", alignItems: "center", justifyContent: "center" }}>RB</div>
                <div>
                  <div style={{ fontFamily: F.ui, fontWeight: 700, fontSize: 32, color: C.carvao }}>Rafa · Barbearia do Centro</div>
                  <div style={{ fontFamily: F.ui, fontSize: 22, color: "#7A766C" }}>online</div>
                </div>
              </div>
              <div style={{ padding: 28, display: "flex", flexDirection: "column", gap: 18 }}>
                {msgs.map((m, i) => {
                  const st = T.s3 + m.at;
                  if (t < st - 0.55) return null;
                  const typing = t < st;
                  const p = spring({ frame: frame - Math.round(st * fps), fps, config: { damping: 14 } });
                  return (
                    <div key={i} style={{ alignSelf: m.me ? "flex-end" : "flex-start", maxWidth: "82%" }}>
                      {typing ? (
                        <div style={{ background: m.me ? "#F3DFA6" : "#fff", borderRadius: 26, padding: "20px 26px", display: "flex", gap: 10 }}>
                          {[0, 1, 2].map((k) => <span key={k} style={{ width: 14, height: 14, borderRadius: 7, background: "#8A857A", transform: `translateY(${Math.sin(t * 12 + k) * 5}px)` }} />)}
                        </div>
                      ) : (
                        <div style={{ background: m.me ? "#F3DFA6" : "#fff", borderRadius: 26, padding: "20px 26px", fontFamily: F.ui, fontSize: 30, lineHeight: 1.35, color: C.carvao, transform: `scale(${0.8 + 0.2 * p})`, transformOrigin: m.me ? "right bottom" : "left bottom", opacity: p, boxShadow: "0 4px 10px rgba(0,0,0,0.06)" }}>
                          {m.me && <div style={{ fontFamily: F.ui, fontWeight: 700, fontSize: 20, color: "#8A6A10", marginBottom: 6 }}>IA · rascunho pra você revisar</div>}
                          {m.text}
                          {m.me && <div style={{ textAlign: "right", fontSize: 20, color: "#3B7BD6", marginTop: 4 }}>✓✓</div>}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {/* ---------- I.V.A. ---------- */}
      <div style={{ position: "absolute", left: ivX, top: ivY + bob + (1 - ivIn) * 700, opacity: (1 - endP) }}>
        <div style={{ position: "absolute", left: ivSize * 0.12, top: ivSize * 0.62, width: ivSize * 0.7, height: 34, borderRadius: "50%", background: "rgba(40,30,10,0.18)", filter: "blur(10px)", transform: `translateY(${180 - bob}px) scale(${1 - bob / 80})` }} />
        <Iva frame={frame} fps={fps} size={ivSize} talking={t < T.end} mood={mood as any} look={t > T.s3 && t < T.s4 ? [1, -0.3] : [0, 0.3]} />
      </div>
      <div style={{ opacity: 1 - endP }}><Pontinho x={dotX} y={dotY} r={ivSize * 0.075} /></div>

      {/* véu claro atrás da legenda (o mundo continua por baixo, como no reel da 6x1) */}
      <div style={{ position: "absolute", left: 0, right: 0, top: 1180, height: 740, opacity: 1 - endP, background: `linear-gradient(180deg, rgba(226,221,207,0) 0%, rgba(226,221,207,0.82) 28%, rgba(222,216,202,0.95) 100%)` }} />
      {/* ---------- legenda ---------- */}
      <div style={{ opacity: 1 - endP }}><Karaoke frame={frame} fps={fps} lines={LINES} y={1330} /></div>

      {/* ---------- cartão final ---------- */}
      {endP > 0 ? (
        <AbsoluteFill style={{ background: C.carvao, opacity: endP, alignItems: "center", justifyContent: "center" }}>
          <EndCard frame={frame - Math.round(T.end * fps)} fps={fps} />
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};

const EndCard: React.FC<{ frame: number; fps: number }> = ({ frame, fps }) => {
  const a = spring({ frame, fps, config: { damping: 14 } });
  const b = spring({ frame: frame - 8, fps, config: { damping: 11 } });
  const c = spring({ frame: frame - 18, fps, config: { damping: 14 } });
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", marginTop: -120 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 20, opacity: a, transform: `translateY(${(1 - a) * 30}px)` }}>
        <svg width={110} height={60} viewBox="0 0 878 481"><path d={CLOUD_PATH} fill={C.papel} fillRule="evenodd" /><circle cx={810} cy={411} r={67} fill={C.ouro} /></svg>
        <div style={{ borderLeft: "2px solid #555", paddingLeft: 20 }}>
          <div style={{ fontFamily: F.display, fontSize: 20, letterSpacing: 5, color: "#BDB7AA" }}>PRODUTO CIELLO:</div>
          <div style={{ fontFamily: F.display, fontWeight: 400, fontSize: 52, letterSpacing: 6, color: C.papel, lineHeight: 1 }}>AUTOMAÇÃO</div>
        </div>
      </div>
      <div style={{ marginTop: 110, fontFamily: F.display, fontWeight: 500, fontSize: 64, color: C.papel, opacity: b }}>Comente</div>
      <div style={{ fontFamily: F.display, fontWeight: 700, fontSize: 210, color: C.ouro, lineHeight: 1, transform: `scale(${0.6 + 0.4 * b})`, opacity: b }}>VENDEDOR</div>
      <div style={{ marginTop: 20, fontFamily: F.ui, fontSize: 40, color: "#CFC9BC", opacity: c }}>e eu te mostro como funciona</div>
      <div style={{ marginTop: 120, fontFamily: F.ui, fontSize: 32, color: "#8E897E", opacity: c }}>
        Seu cliente procura. <span style={{ color: C.ouro }}>A Ciello encontra.</span>
      </div>
    </div>
  );
};
