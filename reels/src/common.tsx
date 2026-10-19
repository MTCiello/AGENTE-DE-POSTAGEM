import React from "react";
import { AbsoluteFill, Easing, interpolate, spring } from "remotion";
import { C, F } from "./theme";
import { U, faceLeft, iso } from "./iso";
import { Iva, IVA_LED, IVA_VB, Pontinho } from "./Iva";
import { CLOUD_PATH } from "./cloudPath";

// ---------- tempo ----------
export const ease = Easing.bezier(0.65, 0, 0.35, 1);
export const kf = (t: number, keys: [number, number][]) =>
  interpolate(t, keys.map((k) => k[0]), keys.map((k) => k[1]), { easing: ease, extrapolateLeft: "clamp", extrapolateRight: "clamp" });
export const sp = (frame: number, fps: number, at: number, damping = 14) =>
  spring({ frame: frame - Math.round(at * fps), fps, config: { damping } });

// ---------- palco ----------
export const Stage: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 42%, ${C.cremeClaro} 0%, ${C.creme} 55%, ${C.cremeEscuro} 100%)`, overflow: "hidden" }}>
    {children}
  </AbsoluteFill>
);
export const SvgDefs = () => (
  <defs>
    <filter id="blur18" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="18" /></filter>
    <filter id="blur8" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="8" /></filter>
  </defs>
);
export const CaptionVeil: React.FC<{ opacity: number }> = ({ opacity }) => (
  <div style={{ position: "absolute", left: 0, right: 0, top: 1180, height: 740, opacity, background: "linear-gradient(180deg, rgba(226,221,207,0) 0%, rgba(226,221,207,0.82) 28%, rgba(222,216,202,0.95) 100%)" }} />
);

// ---------- textos de topo ----------
export const TopTitle: React.FC<{ small: string; big: string; p: number; top?: number; bigSize?: number }> = ({ small, big, p, top = 150, bigSize = 150 }) => (
  <div style={{ position: "absolute", top, width: "100%", textAlign: "center", opacity: p, transform: `translateY(${(1 - p) * -30}px)` }}>
    <div style={{ fontFamily: F.display, fontWeight: 600, fontSize: 40, letterSpacing: 12, color: "#4A4740" }}>{small}</div>
    <div style={{ fontFamily: F.display, fontWeight: 700, fontSize: bigSize, lineHeight: 1.0, color: C.carvao, letterSpacing: -1 }}>{big}</div>
  </div>
);
export const Pill: React.FC<{ a: string; b?: string; p: number; top?: number; size?: number }> = ({ a, b, p, top = 200, size = 34 }) => (
  <div style={{ position: "absolute", top, left: 0, right: 0, display: "flex", justifyContent: "center", opacity: p, transform: `translateY(${(1 - p) * -30}px)` }}>
    <div style={{ background: C.carvao, color: C.branco, borderRadius: 40, padding: "14px 34px", fontFamily: F.display, fontWeight: 500, fontSize: size, letterSpacing: 3 }}>
      {a} {b ? <span style={{ color: C.ouro }}>{b}</span> : null}
    </div>
  </div>
);
export const Chip: React.FC<{ x: number; y: number; p: number; text: string; dot?: string; strike?: number; big?: boolean }> = ({ x, y, p, text, dot, strike = 0, big }) => {
  if (p <= 0.01) return null;
  return (
    <div style={{
      position: "absolute", left: x, top: y, transform: `translate(-50%, -50%) scale(${p})`, background: C.papel, borderRadius: 40,
      padding: big ? "18px 34px" : "12px 26px", display: "flex", alignItems: "center", gap: 12, whiteSpace: "nowrap",
      boxShadow: "0 14px 30px rgba(60,45,20,0.22)", fontFamily: F.display, fontWeight: 600, fontSize: big ? 40 : 30, letterSpacing: 1, color: C.carvao,
    }}>
      {dot ? <span style={{ width: 22, height: 22, borderRadius: 11, background: dot, display: "inline-block" }} /> : null}
      <span style={{ position: "relative" }}>
        {text}
        {strike > 0 ? <span style={{ position: "absolute", left: -6, top: "52%", height: 6, width: `calc(${strike * 100}% + 12px)`, background: C.vermelho, borderRadius: 3 }} /> : null}
      </span>
    </div>
  );
};
// balão de pensamento/fala de uma pessoinha
export const Bubble: React.FC<{ x: number; y: number; p: number; text: string; tone?: "bad" | "good" | "neutral" }> = ({ x, y, p, text, tone = "neutral" }) => {
  if (p <= 0.01) return null;
  const bg = tone === "bad" ? "#FFFFFF" : tone === "good" ? "#F3DFA6" : "#FFFFFF";
  return (
    <div style={{ position: "absolute", left: x, top: y, transform: `translate(-50%, -100%) scale(${p})`, transformOrigin: "50% 100%" }}>
      <div style={{ background: bg, borderRadius: 26, padding: "16px 24px", fontFamily: F.ui, fontWeight: 600, fontSize: 30, color: C.carvao, whiteSpace: "nowrap", boxShadow: "0 12px 26px rgba(60,45,20,0.22)", border: tone === "bad" ? `3px solid ${C.vermelho}` : "none" }}>{text}</div>
      <div style={{ width: 0, height: 0, margin: "0 auto", borderLeft: "14px solid transparent", borderRight: "14px solid transparent", borderTop: `16px solid ${tone === "bad" ? C.vermelho : bg}` }} />
    </div>
  );
};

// ---------- peças isométricas extras ----------
export const Coins: React.FC<{ x: number; y: number; n: number; r?: number }> = ({ x, y, n, r = 0.42 }) => {
  const [sx, sy] = iso(x, y, 0);
  const rx = 1.2247 * r * U, ry = 0.7071 * r * U, hh = 0.13 * U;
  return (
    <g>
      <ellipse cx={sx} cy={sy + 6} rx={rx * 1.2} ry={ry * 1.2} fill="rgba(60,50,30,0.18)" filter="url(#blur8)" />
      {Array.from({ length: Math.max(0, Math.round(n)) }).map((_, i) => (
        <g key={i} transform={`translate(0,${-i * hh})`}>
          <path d={`M ${sx - rx} ${sy} L ${sx - rx} ${sy - hh} A ${rx} ${ry} 0 0 1 ${sx + rx} ${sy - hh} L ${sx + rx} ${sy} A ${rx} ${ry} 0 0 1 ${sx - rx} ${sy} Z`} fill="#B8860F" />
          <ellipse cx={sx} cy={sy - hh} rx={rx} ry={ry} fill={C.ouro} stroke="#C99512" strokeWidth={2} />
          <text x={sx} y={sy - hh + 8} textAnchor="middle" fontFamily={F.display} fontWeight={700} fontSize={22} fill="#9B730C">R$</text>
        </g>
      ))}
    </g>
  );
};
// letreiro sobre o telhado de uma loja (texto na face frontal)
export const Billboard: React.FC<{ x: number; y: number; z: number; w: number; text: string; tone?: "ia" | "real"; flip?: number }> = ({ x, y, z, w, text, tone = "ia", flip = 1 }) => {
  const words = text.split(" ");
  let rows = [text];
  if (text.length > 12 && words.length > 1) {
    let best = 1, diff = 1e9;
    for (let k = 1; k < words.length; k++) { const d = Math.abs(words.slice(0, k).join(" ").length - words.slice(k).join(" ").length); if (d < diff) { diff = d; best = k; } }
    rows = [words.slice(0, best).join(" "), words.slice(best).join(" ")];
  }
  const maxLen = Math.max(...rows.map((r) => r.length));
  const fs = Math.min(0.42, (w * 1.75) / Math.max(6, maxLen));
  const h = rows.length > 1 ? fs * 2 + 0.42 : 0.9;
  const bg = tone === "ia" ? "#F7F4EC" : C.carvao;
  const fg = tone === "ia" ? "#6B6559" : C.ouro;
  const [px, py] = iso(x + w / 2, y, z);
  return (
    <g>
      <line x1={iso(x + 0.3, y, z)[0]} y1={iso(x + 0.3, y, z)[1]} x2={iso(x + 0.3, y, z - 0.3)[0]} y2={iso(x + 0.3, y, z - 0.3)[1]} stroke="#3A3833" strokeWidth={6} />
      <line x1={iso(x + w - 0.3, y, z)[0]} y1={iso(x + w - 0.3, y, z)[1]} x2={iso(x + w - 0.3, y, z - 0.3)[0]} y2={iso(x + w - 0.3, y, z - 0.3)[1]} stroke="#3A3833" strokeWidth={6} />
      <g transform={faceLeft(x, y, z + h)}>
        <g transform={`translate(${w / 2},${h / 2}) scale(1,${flip}) translate(${-w / 2},${-h / 2})`}>
          <rect x={0} y={0} width={w} height={h} fill={bg} stroke={C.carvao} strokeWidth={0.05} />
          {rows.map((r, i) => (
            <text key={i} x={w / 2} y={rows.length > 1 ? 0.21 + fs * (0.86 + i * 1.08) : h * 0.62} textAnchor="middle" fontFamily={F.display} fontWeight={700} fontSize={fs} fill={fg} letterSpacing={0.01}>{r}</text>
          ))}
        </g>
      </g>
      <circle cx={px} cy={py} r={0} />
    </g>
  );
};

// ---------- celular com conversa ----------
export type Msg = { me: boolean; text: string; at: number; tag?: string };
export const PhoneChat: React.FC<{ frame: number; fps: number; t: number; t0: number; p: number; contact: string; initials: string; msgs: Msg[]; label: [string, string]; avatar?: string }> = ({ frame, fps, t, t0, p, contact, initials, msgs, label, avatar = C.verde }) => {
  if (p <= 0.01) return null;
  return (
    <div style={{ position: "absolute", left: 300 + (1 - p) * 600, top: 230, width: 680, height: 1010, transform: `rotate(${(1 - p) * 6}deg)` }}>
      <div style={{ position: "absolute", top: -64, left: 10, fontFamily: F.display, fontWeight: 600, fontSize: 32, letterSpacing: 8, color: "#4A4740" }}>
        {label[0]} <span style={{ color: C.carvao }}>{label[1]}</span>
      </div>
      <div style={{ position: "absolute", inset: 0, borderRadius: 70, background: C.carvao, padding: 16, boxShadow: "0 40px 80px rgba(40,30,10,0.35)" }}>
        <div style={{ position: "absolute", inset: 16, borderRadius: 56, background: "#ECE7DC", overflow: "hidden" }}>
          <div style={{ background: C.papel, padding: "70px 32px 24px", display: "flex", alignItems: "center", gap: 18, borderBottom: "2px solid #DDD6C8" }}>
            <div style={{ width: 70, height: 70, borderRadius: 35, background: avatar, color: "#fff", fontFamily: F.ui, fontWeight: 700, fontSize: 28, display: "flex", alignItems: "center", justifyContent: "center" }}>{initials}</div>
            <div>
              <div style={{ fontFamily: F.ui, fontWeight: 700, fontSize: 32, color: C.carvao }}>{contact}</div>
              <div style={{ fontFamily: F.ui, fontSize: 22, color: "#7A766C" }}>online</div>
            </div>
          </div>
          <div style={{ padding: 26, display: "flex", flexDirection: "column", gap: 16 }}>
            {msgs.map((m, i) => {
              const st = t0 + m.at;
              if (t < st - 0.5) return null;
              const typing = t < st;
              const q = spring({ frame: frame - Math.round(st * fps), fps, config: { damping: 14 } });
              const bg = m.me ? "#F3DFA6" : "#fff";
              return (
                <div key={i} style={{ alignSelf: m.me ? "flex-end" : "flex-start", maxWidth: "84%" }}>
                  {typing ? (
                    <div style={{ background: bg, borderRadius: 26, padding: "20px 26px", display: "flex", gap: 10 }}>
                      {[0, 1, 2].map((k) => <span key={k} style={{ width: 14, height: 14, borderRadius: 7, background: "#8A857A", transform: `translateY(${Math.sin(t * 12 + k) * 5}px)` }} />)}
                    </div>
                  ) : (
                    <div style={{ background: bg, borderRadius: 26, padding: "18px 24px", fontFamily: F.ui, fontSize: 29, lineHeight: 1.35, color: C.carvao, transform: `scale(${0.8 + 0.2 * q})`, transformOrigin: m.me ? "right bottom" : "left bottom", opacity: q, boxShadow: "0 4px 10px rgba(0,0,0,0.06)" }}>
                      {m.tag ? <div style={{ fontFamily: F.ui, fontWeight: 700, fontSize: 20, color: "#8A6A10", marginBottom: 6 }}>{m.tag}</div> : null}
                      {m.text}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

// ---------- I.V.A. como personagem em cena ----------
export const IvaActor: React.FC<{
  frame: number; fps: number; x: number; y: number; size: number; mood: any; talking: boolean; enter: number;
  look?: [number, number]; dot?: { x: number; y: number; away: number } | null; opacity?: number;
}> = ({ frame, fps, x, y, size, mood, talking, enter, look = [0, 0.3], dot, opacity = 1 }) => {
  const t = frame / fps;
  const bob = Math.sin(t * 2.4) * 10;
  const h = (size * IVA_VB.h) / IVA_VB.w;
  const home = { x: x + size * IVA_LED.x, y: y + bob + h * IVA_LED.y };
  const away = dot ? dot.away : 0;
  const dx = home.x + ((dot?.x ?? home.x) - home.x) * away, dy = home.y + ((dot?.y ?? home.y) - home.y) * away;
  return (
    <>
      <div style={{ position: "absolute", left: x, top: y + bob + (1 - enter) * 700, opacity }}>
        <div style={{ position: "absolute", left: size * 0.1, top: size * 0.86, width: size * 0.8, height: 30, borderRadius: "50%", background: "rgba(40,30,10,0.18)", filter: "blur(10px)", transform: `translateY(${60 - bob}px) scale(${1 - bob / 80})` }} />
        <Iva frame={frame} fps={fps} size={size} talking={talking} mood={mood} look={look} ledOn={away < 0.05} />
      </div>
      {away > 0.02 ? <div style={{ opacity }}><Pontinho x={dx} y={dy} r={size * (0.02 + 0.045 * away)} /></div> : null}
    </>
  );
};

// ---------- cartão final ----------
export const EndCard: React.FC<{ frame: number; fps: number; product: string; word: string; sub: string; foot: [string, string] }> = ({ frame, fps, product, word, sub, foot }) => {
  const a = spring({ frame, fps, config: { damping: 14 } });
  const b = spring({ frame: frame - 8, fps, config: { damping: 11 } });
  const c = spring({ frame: frame - 18, fps, config: { damping: 14 } });
  const ws = word.length > 8 ? 1500 / word.length : 200;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", marginTop: -120 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 20, opacity: a, transform: `translateY(${(1 - a) * 30}px)` }}>
        <svg width={110} height={60} viewBox="0 0 878 481"><path d={CLOUD_PATH} fill={C.papel} fillRule="evenodd" /><circle cx={810} cy={411} r={67} fill={C.ouro} /></svg>
        <div style={{ borderLeft: "2px solid #555", paddingLeft: 20 }}>
          <div style={{ fontFamily: F.display, fontSize: 20, letterSpacing: 5, color: "#BDB7AA" }}>PRODUTO CIELLO:</div>
          <div style={{ fontFamily: F.display, fontWeight: 400, fontSize: 52, letterSpacing: 6, color: C.papel, lineHeight: 1 }}>{product}</div>
        </div>
      </div>
      <div style={{ marginTop: 110, fontFamily: F.display, fontWeight: 500, fontSize: 64, color: C.papel, opacity: b }}>Comente</div>
      <div style={{ fontFamily: F.display, fontWeight: 700, fontSize: ws, color: C.ouro, lineHeight: 1, transform: `scale(${0.6 + 0.4 * b})`, opacity: b }}>{word}</div>
      <div style={{ marginTop: 20, fontFamily: F.ui, fontSize: 40, color: "#CFC9BC", opacity: c }}>{sub}</div>
      <div style={{ marginTop: 120, fontFamily: F.ui, fontSize: 32, color: "#8E897E", opacity: c }}>
        {foot[0]} <span style={{ color: C.ouro }}>{foot[1]}</span>
      </div>
    </div>
  );
};
export const EndLayer: React.FC<{ p: number; children: React.ReactNode }> = ({ p, children }) =>
  p > 0 ? <AbsoluteFill style={{ background: C.carvao, opacity: p, alignItems: "center", justifyContent: "center" }}>{children}</AbsoluteFill> : null;
