import React from "react";
import { AbsoluteFill, Easing, useCurrentFrame, useVideoConfig } from "remotion";
import { C, F } from "../theme";
import {
  Bloco, CardLegenda, Cinetico, Contador, IconeConversa, Janela, MarcaCiello, Papel, Pilula, Sombra, TXT, camera, entre, mix, mixCor, mola,
} from "./kit";

// "A conversa que não se perde" — reel do CIELLO CRM em plano-sequência.
// O fio que atravessa tudo: as mensagens perdidas do começo viram os cards do funil, a rede da equipe
// se recolhe num ponto dourado e esse ponto pousa no "Comenta" do final.
export const CRM_PLANO = { total: 30.5 };

const BOLHAS = [
  { txt: "Oi, qual o valor?", nome: "Carla", valor: 4800, sx: 560, sy: 96, r: -6 },
  { txt: "Ainda tem disponível?", nome: "Marcos", valor: 2300, sx: 760, sy: 170, r: 5 },
  { txt: "Me manda o orçamento", nome: "Júlia", valor: 1650, sx: 330, sy: 54, r: 3 },
  { txt: "Alguém aí?", nome: "Pedro", valor: 900, sx: 640, sy: 220, r: -4 },
  { txt: "Faz parcelado?", nome: "Ana", valor: 3200, sx: 860, sy: 70, r: 8 },
  { txt: "Vi no Instagram", nome: "Rafa", valor: 1200, sx: 380, sy: 200, r: -2 },
  { txt: "??", sx: 960, sy: 230, r: 10 },
  { txt: "Oi", sx: 250, sy: 170, r: -9 },
  { txt: "Bom dia!", sx: 650, sy: 22, r: 4 },
];

// janela do CRM e suas colunas
const JX = 80, JY = 360, JW = 920, JH = 820;
const COLW = (JW - 48 - 42) / 4;
const colX = (i: number) => JX + 24 + i * (COLW + 14);
const slotY = (j: number) => JY + 58 + 128 + j * 78;
const COLUNAS = ["Novo", "Em conversa", "Proposta", "Fechado"];

const Bolha: React.FC<{ txt: string }> = ({ txt }) => (
  <div style={{ background: "#FFFFFF", borderRadius: 22, borderBottomLeftRadius: 6, padding: "14px 22px", boxShadow: Sombra, whiteSpace: "nowrap",
    fontFamily: "Inter, sans-serif", fontWeight: 700, fontSize: 28, color: TXT.escuro }}>
    {txt}
  </div>
);

const Card: React.FC<{ nome: string; valor: number; destaque?: boolean }> = ({ nome, valor, destaque }) => (
  <div style={{ width: COLW - 16, height: 64, borderRadius: 14, background: "#262423", border: `2px solid ${destaque ? C.ouro : "#34312e"}`,
    padding: "8px 14px", boxSizing: "border-box", fontFamily: "Inter, sans-serif", boxShadow: destaque ? "0 0 24px rgba(224,168,28,0.35)" : "none" }}>
    <div style={{ fontWeight: 800, fontSize: 21, color: "#F2EEE6" }}>{nome}</div>
    <div style={{ fontWeight: 700, fontSize: 18, color: C.ouro }}>R$ {valor.toLocaleString("pt-BR")}</div>
  </div>
);

const Celular: React.FC<{ nome: string }> = ({ nome }) => (
  <div style={{ width: 150, height: 270, borderRadius: 28, background: "#1A1918", padding: 8, boxShadow: Sombra }}>
    <div style={{ width: "100%", height: "100%", borderRadius: 22, background: "#F7F4EC", padding: 12, boxSizing: "border-box", display: "flex", flexDirection: "column", gap: 10 }}>
      {[70, 90, 55].map((w, i) => (
        <div key={i} style={{ alignSelf: i % 2 ? "flex-end" : "flex-start", width: `${w}%`, height: 26, borderRadius: 10, background: i % 2 ? "#DCEFE3" : "#FFFFFF", boxShadow: "0 2px 4px rgba(0,0,0,0.06)" }} />
      ))}
      <div style={{ marginTop: "auto", fontFamily: "Inter, sans-serif", fontWeight: 800, fontSize: 17, color: TXT.escuro, textAlign: "center" }}>{nome}</div>
    </div>
  </div>
);

export const CrmPlano: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  // ---------------------------------------------------------------- tempos das viradas
  const SAI0 = 4.2, CARD = 6.5, MORPH = 7.3, VOA = 8.2, MOVE = [10.6, 11.5, 12.4], SAIJ = 13.8, OBJ = 15.0, RISCA = 17.0, HUB = 19.6, JUNTA = 23.7, CTA = 24.4;
  const cam = camera(t, [
    [0, 0, 0, 1], [7.4, 0, 0, 1], [9.5, 0, -20, 1.03], [10.4, 0, -20, 1.03], [10.9, 60, -300, 1.22], [12.9, 140, -300, 1.22], [13.5, 0, -20, 1.03],
    [15, 0, 0, 1], [17.3, 0, 0, 1], [17.65, 0, -150, 1.14], [18.9, 0, -150, 1.14], [19.35, 0, 0, 1], // soco no risco
    [23.5, 0, 0, 1], [24.15, 0, -220, 1.55], [24.85, 0, 0, 1], // entra no ponto dourado e abre no CTA
    [26.5, 0, 0, 1], [26.75, 0, -120, 1.08], [27.5, 0, -40, 1.02], [30.5, 0, -40, 1.02],
  ], [8.9, 10.9, MOVE[2], 13.5, 17.65, 24.85, 26.75]);

  // ---------------------------------------------------------------- cena 0: as conversas se perdendo
  const saida0 = entre(t, SAI0, SAI0 + 0.45, Easing.in(Easing.cubic));
  const kChat = mola(t, fps, 0.1), kLogo = mola(t, fps, 0.35);
  const linha = entre(t, 0.6, 1.2);

  // ---------------------------------------------------------------- cena 1 → 2: o card nasce do "COMO" e vira o CRM
  const cresce = entre(t, CARD, MORPH, Easing.bezier(0.2, 0.8, 0.2, 1));
  const morph = entre(t, MORPH, MORPH + 0.6);
  const saiJ = entre(t, SAIJ, SAIJ + 0.7, Easing.in(Easing.cubic));
  const janelaVisivel = t >= CARD && t < SAIJ + 0.8;
  const caixa = { x: mix(80, JX, cresce), y: mix(960, JY, cresce), w: mix(380, JW, cresce), h: mix(150, JH, cresce) };

  // card destacado andando pelas colunas
  const passo = MOVE.reduce((s, m) => s + mola(t, fps, m, 15, 150), 0); // 0 → 3
  const colDestaque = Math.min(3, passo);
  const noFunil = (i: number) => entre(t, VOA + i * 0.09, VOA + i * 0.09 + 0.75, Easing.bezier(0.5, 0, 0.2, 1));
  const chegaram = BOLHAS.slice(0, 6).filter((_, i) => noFunil(i) >= 1).length;
  const sobe = mola(t, fps, MOVE[0], 18, 140); // os outros cards sobem quando o 1º sai de "Novo"

  // ---------------------------------------------------------------- cena 4: a equipe em rede
  const CENTRO = { x: 540, y: 700 };
  const FONES = [{ x: 210, y: 470, nome: "Ana · vendas" }, { x: 870, y: 470, nome: "Léo · vendas" }, { x: 210, y: 960, nome: "Bia · pós-venda" }, { x: 870, y: 960, nome: "Você · gestão" }];
  const junta = entre(t, JUNTA, JUNTA + 0.55, Easing.in(Easing.cubic));
  const pontoVoa = entre(t, JUNTA + 0.35, CTA + 0.3, Easing.bezier(0.6, 0, 0.2, 1));

  return (
    <AbsoluteFill>
      <Papel t={t} />
      <AbsoluteFill style={{ transform: cam, transformOrigin: "540px 900px" }}>
        {/* ===== cena 0 ===== */}
        {t < SAI0 + 0.5 ? (
          <div style={{ transform: `translateY(${-saida0 * 1300}px)`, filter: `blur(${Math.sin(saida0 * Math.PI) * 8}px)` }}>
            <svg width={1080} height={700} style={{ position: "absolute", left: 0, top: 0 }}>
              <path d="M385 420 H695" stroke={C.ouro} strokeWidth={5} strokeDasharray="2 14" strokeLinecap="round" opacity={linha} strokeDashoffset={-t * 60} />
              {[0, 0.33, 0.66].map((o) => {
                const p = (t * 0.7 + o) % 1;
                return t > 1.2 ? <circle key={o} cx={385 + 310 * p} cy={420} r={9} fill={C.ouro} opacity={Math.sin(p * Math.PI)} /> : null;
              })}
            </svg>
            <Bloco x={300} y={420} tam={170} k={kChat}><IconeConversa tam={96} /></Bloco>
            <Bloco x={780} y={420} tam={170} k={kLogo}><MarcaCiello largura={118} /></Bloco>
            <div style={{ position: "absolute", left: 700, top: 528, transform: `scale(${mola(t, fps, 0.9)})`, background: "#fff", borderRadius: 999, padding: "8px 18px",
              boxShadow: Sombra, fontFamily: "monospace", fontSize: 24, color: TXT.medio }}>
              conversas: <b style={{ color: TXT.escuro }}><Contador t={t} de={0} ate={47} a={0.9} b={3.8} /></b>
            </div>
            <Cinetico t={t} fps={fps} texto="Seu WhatsApp tá *perdendo* *venda*" inicio={0.25} y={650} tamanho={96} />
            <Pilula x={80} y={890} k={mola(t, fps, 2.9)} texto="orçamento esquecido" tipo="nao" />
            <Pilula x={80} y={974} k={mola(t, fps, 3.3)} texto="cliente sem resposta" tipo="nao" />
          </div>
        ) : null}

        {/* bolhas: espalham na cena 0, esperam apagadas na cena 1 e voam para o funil na cena 2 */}
        {t < SAIJ + 0.8
          ? BOLHAS.map((b, i) => {
              const k = mola(t, fps, 1.2 + i * 0.12, 13, 120);
              const espera = entre(t, 4.6, 5.2);
              const vai = i < 6 ? noFunil(i) : 0;
              const some = i >= 6 ? entre(t, VOA - 0.3, VOA) : 0;
              if (k <= 0.01 || vai >= 1) return null;
              const x0 = mix(1180, b.sx, k), y0 = mix(-160, b.sy, k) - espera * 30;
              const x = mix(x0, colX(0) + 8, vai), y = mix(y0, slotY(i), vai);
              const vel = vai > 0 && vai < 1 ? 14 * Math.sin(vai * Math.PI) : 0;
              return (
                <div key={i} style={{ position: "absolute", left: x, top: y, transform: `rotate(${mix(b.r, 0, vai)}deg) scale(${mix(1, 0.8, vai)})`, transformOrigin: "left top",
                  opacity: Math.min(1, k * 2) * (1 - espera * 0.55 + entre(t, VOA - 0.2, VOA) * 0.55) * (1 - some), filter: `blur(${vel * 0.5}px)` }}>
                  <Bolha txt={b.txt} />
                </div>
              );
            })
          : null}

        {/* ===== cena 1 ===== */}
        {t >= 4.6 && t < MORPH + 0.2 ? (
          <div style={{ opacity: 1 - entre(t, CARD, CARD + 0.3), transform: `translateY(${(1 - mola(t, fps, 4.55, 15, 120)) * 700}px)` }}>
            <div style={{ position: "absolute", left: 80, top: 900, fontFamily: F.display, fontWeight: 500, fontSize: 32, letterSpacing: 10, color: TXT.medio, opacity: mola(t, fps, 4.8) }}>
              DEIXA EU TE MOSTRAR
            </div>
            <Cinetico t={t} fps={fps} texto="COMO" inicio={5.1} y={950} tamanho={150} peso={900} />
          </div>
        ) : null}

        {/* ===== cena 2: o CRM ===== */}
        {janelaVisivel ? (
          <div style={{ transform: `perspective(1800px) translateX(${-saiJ * 1000}px) rotateY(${-saiJ * 28}deg) scale(${1 - saiJ * 0.1})`, filter: `blur(${saiJ * 9}px)`, opacity: 1 - entre(t, SAIJ + 0.4, SAIJ + 0.7) }}>
            <Janela x={caixa.x} y={caixa.y} w={caixa.w} h={caixa.h} morph={morph} titulo="CIELLO CRM · funil de vendas">
              <div style={{ position: "absolute", right: 24, top: 18, fontFamily: F.ui, fontSize: 18, color: "#6f6a62", border: "1px solid #3a3734", borderRadius: 8, padding: "2px 10px" }}>exemplo</div>
              {COLUNAS.map((c, i) => {
                const n = i === 0 ? Math.max(0, chegaram - (colDestaque > 0.5 ? 1 : 0)) : Math.round(colDestaque) === i ? 1 : 0;
                return (
                  <div key={c} style={{ position: "absolute", left: colX(i) - JX, top: 82, width: COLW, height: JH - 120, borderRadius: 16, background: "#211F1E" }}>
                    <div style={{ padding: "12px 16px", fontFamily: "Inter, sans-serif", display: "flex", flexDirection: "column", gap: 2 }}>
                      <span style={{ fontWeight: 700, fontSize: 21, color: "#A7A196" }}>{c}</span>
                      <span style={{ fontWeight: 800, fontSize: i === 3 ? 22 : 24, color: i === 3 ? C.ouro : "#F2EEE6" }}>
                        {i === 3 ? <Contador t={t} de={0} ate={4800} a={MOVE[2] + 0.1} b={MOVE[2] + 0.8} prefixo="R$ " /> : n}
                      </span>
                    </div>
                  </div>
                );
              })}
            </Janela>
            {/* cards que chegaram (fora da janela para poder andar entre colunas) */}
            {BOLHAS.slice(0, 6).map((b, i) => {
              if (noFunil(i) < 1) return null;
              if (i === 0) {
                const x = mix(colX(Math.floor(colDestaque)), colX(Math.min(3, Math.floor(colDestaque) + 1)), colDestaque % 1) + 8;
                const pulo = Math.sin((colDestaque % 1) * Math.PI) * 110;
                return <div key={i} style={{ position: "absolute", left: x, top: slotY(0) - pulo, zIndex: 5 }}><Card nome={b.nome!} valor={b.valor!} destaque /></div>;
              }
              return <div key={i} style={{ position: "absolute", left: colX(0) + 8, top: slotY(i) - sobe * 78 }}><Card nome={b.nome!} valor={b.valor!} /></div>;
            })}
            <CardLegenda x={JX} y={1215} w={JW} k={mola(t, fps, VOA)}>
              <div style={{ position: "relative", height: 112 }}>
                <Cinetico t={t} fps={fps} texto="No CIELLO CRM, toda conversa vira *um* *card* *no* *funil*" inicio={VOA + 0.1} x={0} y={0} largura={850} tamanho={44} porPalavra={0.1} sai={10.5} />
                <Cinetico t={t} fps={fps} texto="e você vê *quanto* *tem* *pra* *fechar* no mês." inicio={10.9} x={0} y={0} largura={850} tamanho={44} porPalavra={0.1} />
              </div>
            </CardLegenda>
          </div>
        ) : null}

        {/* ===== cena 3: a objeção riscada, num painel escuro que atravessa a tela ===== */}
        {t >= OBJ - 0.4 && t < HUB + 0.2 ? (
          <div style={{ transform: `translateX(${(1 - mola(t, fps, OBJ - 0.35, 17, 110)) * 1100 - entre(t, HUB - 0.5, HUB, Easing.in(Easing.cubic)) * 1250}px) rotate(${-entre(t, HUB - 0.5, HUB) * 4}deg)`,
            filter: `blur(${Math.sin(entre(t, HUB - 0.5, HUB) * Math.PI) * 8}px)` }}>
            <div style={{ position: "absolute", left: 50, top: 720, width: 980, height: 600, borderRadius: 34, background: "#1A1918", boxShadow: "0 40px 80px rgba(40,30,15,0.28)" }} />
            <Cinetico t={t} fps={fps} texto="Você deve estar pensando" inicio={OBJ} x={110} y={790} tamanho={42} peso={600} cor="#A7A196" />
            <Cinetico t={t} fps={fps} texto="que a equipe" inicio={OBJ + 0.6} x={110} y={866} tamanho={100} cor="#F2EEE6" corRisco="#F2EEE6" riscado={entre(t, RISCA, RISCA + 0.3)} />
            <Cinetico t={t} fps={fps} texto="não vai usar" inicio={OBJ + 0.95} x={110} y={976} tamanho={100} cor="#F2EEE6" corRisco="#F2EEE6" riscado={entre(t, RISCA + 0.2, RISCA + 0.5)} />
            <Pilula x={110} y={1150} k={mola(t, fps, RISCA + 0.6, 11, 160)} texto="funciona no celular de cada um." tipo="ouro" tam={46} giro={-2} />
          </div>
        ) : null}

        {/* ===== cena 4: a equipe em rede, que se recolhe num ponto ===== */}
        {t >= HUB && t < CTA + 0.4 ? (
          <>
            <svg width={1080} height={1300} style={{ position: "absolute", left: 0, top: 0 }}>
              {FONES.map((f, i) => {
                const d = entre(t, HUB + 0.3 + i * 0.1, HUB + 0.9 + i * 0.1);
                const fx = mix(f.x, CENTRO.x, junta), fy = mix(f.y, CENTRO.y, junta);
                const len = Math.hypot(fx - CENTRO.x, fy - CENTRO.y);
                const p = (t * 0.55 + i * 0.27) % 1;
                return (
                  <g key={i} opacity={1 - junta}>
                    <line x1={CENTRO.x} y1={CENTRO.y} x2={fx} y2={fy} stroke={C.ouro} strokeWidth={4} strokeDasharray={`${len * d} ${len}`} />
                    {t > HUB + 1 ? <circle cx={mix(CENTRO.x, fx, p)} cy={mix(CENTRO.y, fy, p)} r={8} fill={C.ouro} /> : null}
                  </g>
                );
              })}
            </svg>
            {FONES.map((f, i) => {
              const k = mola(t, fps, HUB + 0.3 + i * 0.12);
              return (
                <div key={i} style={{ position: "absolute", left: mix(mix(f.x < 540 ? -300 : 1380, f.x, k), CENTRO.x, junta) - 75, top: mix(mix(f.y < 700 ? -400 : 2200, f.y, k), CENTRO.y, junta) - 135, transform: `scale(${k * (1 - junta)}) rotate(${(i % 2 ? 4 : -4) * (1 - k)}deg)` }}>
                  <Celular nome={f.nome} />
                </div>
              );
            })}
            {FONES.map((f, i) => (
              <Pilula key={`p${i}`} x={f.x + (i % 2 ? -150 : 40)} y={f.y - 190} k={mola(t, fps, HUB + 1.4 + i * 0.55) * (1 - junta)} texto="+1 conversa" tipo="ok" tam={22} />
            ))}
            {/* o centro vira o ponto dourado que voa para o "Comenta" */}
            {(() => {
              const k = mola(t, fps, HUB);
              const vira = entre(t, JUNTA + 0.2, JUNTA + 0.5);
              const x = mix(CENTRO.x, 112, pontoVoa), y = mix(CENTRO.y, 922, pontoVoa);
              const tam = mix(200, 52, vira);
              return (
                <div style={{ position: "absolute", left: x - tam / 2, top: y - tam / 2, width: tam, height: tam, borderRadius: mix(52, 26, vira),
                  background: mixCor("#FFFFFF", C.ouro, vira), boxShadow: Sombra, transform: `scale(${k})`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <div style={{ opacity: 1 - vira }}><MarcaCiello largura={140} /></div>
                </div>
              );
            })()}
            <Cinetico t={t} fps={fps} texto="A equipe toda no *mesmo* *número*, cada um no seu celular." inicio={HUB + 0.5} y={1180} tamanho={60} porPalavra={0.1} sai={JUNTA} />
          </>
        ) : null}

        {/* ===== cena 5: CTA ===== */}
        {t >= CTA ? (
          <>
            <Cinetico t={t} fps={fps} texto="Quer testar *30* *dias* *grátis*?" inicio={CTA + 0.1} y={780} tamanho={50} peso={700} cor={TXT.medio} />
            {t >= CTA + 0.3 ? <div style={{ position: "absolute", left: 112 - 26, top: 922 - 26, width: 52, height: 52, borderRadius: 26, background: C.ouro }} /> : null}
            <Cinetico t={t} fps={fps} texto="Comenta" inicio={CTA + 0.45} x={170} y={850} tamanho={130} peso={900} />
            {(() => {
              const k = mola(t, fps, CTA + 0.9);
              const txt = "CRM".slice(0, Math.max(0, Math.floor((t - (CTA + 1.2)) / 0.2)));
              const publicado = t > CTA + 2.2;
              const caret = Math.floor(t * 2.5) % 2 === 0 && !publicado;
              return (
                <div style={{ position: "absolute", left: 80, top: 1040, width: 920, height: 112, borderRadius: 60, background: "#FFFFFF", boxShadow: Sombra,
                  display: "flex", alignItems: "center", padding: "0 18px 0 22px", gap: 20, transform: `scale(${k})`, opacity: Math.min(1, k * 2) }}>
                  <div style={{ width: 70, height: 70, borderRadius: 35, background: "#EDE7DA", display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <MarcaCiello largura={44} />
                  </div>
                  <div style={{ flex: 1, fontFamily: "Inter, sans-serif", fontWeight: 900, fontSize: 44, color: TXT.escuro, letterSpacing: 1 }}>
                    {txt}{caret ? <span style={{ color: C.ouro }}>|</span> : null}
                  </div>
                  <div style={{ fontFamily: "Inter, sans-serif", fontWeight: 800, fontSize: 30, color: publicado ? C.verde : "#3E7BD9", paddingRight: 18 }}>
                    {publicado ? "Publicado ✓" : "Publicar"}
                  </div>
                </div>
              );
            })()}
            <div style={{ position: "absolute", left: 110, top: 1186, fontFamily: "monospace", fontSize: 22, letterSpacing: 6, color: C.ouro, opacity: mola(t, fps, CTA + 2.5) }}>RESPOSTA AUTOMÁTICA</div>
            <Pilula x={80} y={1230} k={mola(t, fps, CTA + 2.7, 12, 160)} texto="✉  DM enviada: seu acesso de 30 dias" tipo="ouro" tam={38} />
            <div style={{ position: "absolute", left: 0, width: 1080, top: 1340, textAlign: "center", fontFamily: "Inter, sans-serif", fontWeight: 600, fontSize: 32, color: TXT.leve, opacity: mola(t, fps, CTA + 3.4) }}>
              chega no seu direct →
            </div>
          </>
        ) : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
