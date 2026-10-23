import React from "react";
import { AbsoluteFill, Easing, useCurrentFrame, useVideoConfig } from "remotion";
import { C, F } from "../theme";
import { Bloco, CardLegenda, Cinetico, Contador, MarcaCiello, Papel, Pilula, Sombra, TXT, camera, entre, mix, mixCor, mola } from "./kit";

// "3 comandos do ChatGPT que respondem cliente por você" — plano-sequência do pilar Comandos.
// O fio: o cursor dourado do gancho cresce e vira a janela do chat; a janela atravessa os 3 comandos
// (a conversa rola, nunca troca de tela) e sai de cena para a ponte com o CRM; o final pede o salvamento.
export const COMANDOS_PLANO = { total: 29.5 };

const JX = 70, JY = 430, JW = 940, JH = 900;
const AREA = { top: 80, h: JH - 80 - 150 }; // área das mensagens dentro da janela

type Bloco = { quem: "eu" | "ia"; altura: number; render: (k: number) => React.ReactNode };

const COMANDOS = [
  {
    rotulo: ["COMANDO 1", "tom de atendimento"], legenda: "Ele responde o cliente *no* *seu* *tom*.",
    prompt: "Responda como atendente da minha loja: educado, curto e sempre com uma pergunta no final.",
    digita: 4.5, envia: 7.0, resposta: 7.4,
  },
  {
    rotulo: ["COMANDO 2", "orçamento pronto"], legenda: "A conversa vira *orçamento* em segundos.",
    prompt: "Transforme esta conversa em um orçamento com itens, valor e prazo.",
    digita: 11.4, envia: 13.2, resposta: 13.6,
  },
  {
    rotulo: ["COMANDO 3", "cliente que sumiu"], legenda: "E recupera quem *sumiu* *depois* *do* *orçamento*.",
    prompt: "Escreva 3 mensagens curtas para o cliente que sumiu depois do orçamento.",
    digita: 16.9, envia: 18.6, resposta: 19.0,
  },
];

const RESPOSTA_1 = "Oi, Ana! Temos sim 😊 O tamanho M sai por R$ 89 e chega amanhã. Prefere retirar na loja ou receber em casa?";
const ITENS = [["Mesa de jantar 6 lugares", 1890], ["6 cadeiras estofadas", 1740], ["Frete e montagem", 180]] as const;
const RECUPERA = ["Oi, Carla! Ainda faz sentido a mesa pra vocês? 🙂", "Consegui segurar o valor até sexta, quer que eu reserve?", "Se preferir, mando opções em outra faixa de preço."];

const texto = (s: string, t: number, t0: number, cps: number) => s.slice(0, Math.max(0, Math.floor((t - t0) * cps)));

export const ComandosPlano: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const VIRA = 3.3, SAIJ = 21.6, PONTE = 22.0, CTA = 25.2;
  const cam = camera(t, [
    [0, 0, 0, 1], [3.3, 0, 30, 1.03], [4.4, 0, 0, 1],
    [7.9, 0, -50, 1.04], [8.25, 0, -230, 1.2], [10.6, 0, -210, 1.18], [11.0, 0, 0, 1], // aproxima digitando, soco na resposta 1
    [14.1, 0, -50, 1.04], [14.45, 0, -200, 1.18], [16.3, 0, -180, 1.16], [16.7, 0, 0, 1], // soco no orçamento
    [19.5, 0, -50, 1.04], [19.85, 0, -220, 1.2], [21.3, 0, -200, 1.18], [21.7, 0, 0, 1], // soco nas mensagens
    [24.8, 0, -60, 1.06], [25.3, 0, 0, 1], [29.5, 0, 0, 1.02], // ponte com aproximação lenta e respiro no fim
  ], [8.25, 14.45, 19.85, CTA + 0.6]);

  // ---------------------------------------------------------------- gancho e cursor que vira janela
  const sai0 = entre(t, VIRA, VIRA + 0.45, Easing.in(Easing.cubic));
  const cresce = entre(t, VIRA + 0.1, VIRA + 1.0, Easing.bezier(0.2, 0.8, 0.2, 1));
  const conteudo = entre(t, VIRA + 0.8, VIRA + 1.2);
  const saiJ = entre(t, SAIJ, SAIJ + 0.65, Easing.in(Easing.cubic));
  const caixa = { x: mix(866, JX, cresce), y: mix(812, JY, cresce), w: mix(12, JW, cresce), h: mix(96, JH, cresce) };

  // ---------------------------------------------------------------- conversa (rola, nunca troca de tela)
  const blocos: (Bloco & { at: number })[] = [];
  COMANDOS.forEach((c, i) => {
    blocos.push({ quem: "eu", altura: 150, at: c.envia, render: () => <span>{c.prompt}</span> });
    if (i === 0) blocos.push({ quem: "ia", altura: 200, at: c.resposta, render: () => <span>{texto(RESPOSTA_1, t, c.resposta, 70)}</span> });
    if (i === 1)
      blocos.push({
        quem: "ia", altura: 330, at: c.resposta, render: () => (
          <div style={{ width: 600 }}>
            <div style={{ fontWeight: 800, fontSize: 26, color: C.ouro, marginBottom: 12 }}>Orçamento · Móveis Bela Casa</div>
            {ITENS.map(([nome, v], j) => (
              <div key={nome} style={{ display: "flex", justifyContent: "space-between", fontSize: 25, padding: "8px 0", borderBottom: "1px solid #3a3734",
                opacity: entre(t, c.resposta + 0.2 + j * 0.25, c.resposta + 0.45 + j * 0.25) }}>
                <span>{nome}</span><span>R$ {v.toLocaleString("pt-BR")}</span>
              </div>
            ))}
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 14, fontWeight: 800, fontSize: 30 }}>
              <span>Total · entrega em 7 dias</span>
              <span style={{ color: C.ouro }}><Contador t={t} de={0} ate={3810} a={c.resposta + 0.9} b={c.resposta + 1.6} prefixo="R$ " /></span>
            </div>
          </div>
        ),
      });
    if (i === 2)
      blocos.push({
        quem: "ia", altura: 300, at: c.resposta, render: () => (
          <div style={{ display: "flex", flexDirection: "column", gap: 12, width: 640 }}>
            {RECUPERA.map((m, j) => {
              const k = mola(t, fps, c.resposta + 0.15 + j * 0.35, 14, 150);
              return (
                <div key={j} style={{ background: "#2E3B2F", borderRadius: 18, padding: "14px 18px", fontSize: 25, transform: `translateX(${(1 - k) * 60}px)`, opacity: Math.min(1, k * 2) }}>
                  <b style={{ color: "#7FD39B" }}>{j + 1}.</b> {m}
                </div>
              );
            })}
          </div>
        ),
      });
  });
  // rolagem: cada comando novo empurra a conversa para cima
  let topo = 0;
  const posicoes = blocos.map((b) => { const y = topo; topo += b.altura + 26; return y; });
  const alvo = (i: number) => -posicoes[i * 2];
  const rolagem = COMANDOS.reduce((s, c, i) => (i === 0 ? s : s + (alvo(i) - alvo(i - 1)) * mola(t, fps, c.envia - 0.05, 18, 120)), 0);

  const atual = COMANDOS.reduce((s, c, i) => (t >= c.digita - 0.5 ? i : s), 0);
  const cmd = COMANDOS[atual];
  const digitando = t >= cmd.digita && t < cmd.envia ? texto(cmd.prompt, t, cmd.digita, 48) : "";
  const cursorPisca = Math.floor(t * 2.5) % 2 === 0;

  return (
    <AbsoluteFill>
      <Papel t={t} />
      <AbsoluteFill style={{ transform: cam, transformOrigin: "540px 880px" }}>
        {/* ===== gancho ===== */}
        {t < VIRA + 0.6 ? (
          <div style={{ transform: `translateY(${-sai0 * 1200}px)`, filter: `blur(${Math.sin(sai0 * Math.PI) * 8}px)` }}>
            <Pilula x={80} y={560} k={mola(t, fps, 0.15)} texto="IA PRO SEU NEGÓCIO" tipo="ouro" tam={30} />
            <Cinetico t={t} fps={fps} texto="3 comandos do ChatGPT que *respondem* *cliente* por você" inicio={0.35} y={650} tamanho={92} porPalavra={0.12} largura={930} />
            <Cinetico t={t} fps={fps} texto="Salva antes de fechar o vídeo." inicio={2.0} y={1110} tamanho={42} peso={600} cor={TXT.medio} />
          </div>
        ) : null}
        {/* o cursor dourado que pisca no fim do gancho e cresce até virar a janela */}
        {t >= 1.6 && t < SAIJ + 0.8 ? (
          <div style={{ transform: `perspective(1800px) translateX(${-saiJ * 1100}px) rotateY(${-saiJ * 26}deg)`, filter: `blur(${saiJ * 9}px)`, opacity: 1 - entre(t, SAIJ + 0.4, SAIJ + 0.7) }}>
            <div style={{ position: "absolute", left: caixa.x, top: caixa.y, width: caixa.w, height: caixa.h, borderRadius: mix(4, 28, cresce), overflow: "hidden",
              background: mixCor(C.ouro, "#1A1918", entre(cresce, 0.2, 0.7)), boxShadow: cresce > 0.3 ? "0 40px 80px rgba(40,30,15,0.28)" : "none",
              opacity: cresce > 0 ? 1 : (cursorPisca ? 1 : 0.15) * mola(t, fps, 1.6) }}>
              <div style={{ opacity: conteudo, fontFamily: "Inter, sans-serif", color: "#F2EEE6" }}>
                <div style={{ height: 66, display: "flex", alignItems: "center", gap: 12, padding: "0 26px", borderBottom: "1px solid #2c2a28" }}>
                  {["#FF5F57", "#FEBC2E", "#28C840"].map((c) => <span key={c} style={{ width: 16, height: 16, borderRadius: "50%", background: c }} />)}
                  <span style={{ marginLeft: 16, fontSize: 23, color: "#8E897E" }}>Chat com IA</span>
                  <span style={{ marginLeft: "auto", fontSize: 18, color: "#6f6a62", border: "1px solid #3a3734", borderRadius: 8, padding: "2px 10px" }}>exemplo</span>
                </div>
                <div style={{ position: "absolute", left: 30, right: 30, top: AREA.top, height: AREA.h, overflow: "hidden" }}>
                  <div style={{ transform: `translateY(${rolagem}px)` }}>
                    {blocos.map((b, i) => {
                      const k = mola(t, fps, b.at, 15, 150);
                      if (t < b.at) return null;
                      const eu = b.quem === "eu";
                      return (
                        <div key={i} style={{ position: "absolute", top: posicoes[i], left: eu ? undefined : 0, right: eu ? 0 : undefined, maxWidth: 700,
                          transform: `translateY(${(1 - k) * 30}px)`, opacity: Math.min(1, k * 2) }}>
                          <div style={{ background: eu ? "#3A3220" : "#262423", border: `1px solid ${eu ? "#5a4a1f" : "#34312e"}`, borderRadius: 22,
                            borderBottomRightRadius: eu ? 6 : 22, borderBottomLeftRadius: eu ? 22 : 6, padding: "18px 22px", fontSize: 27, lineHeight: 1.35 }}>
                            {b.render(k)}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
                {/* caixa de digitação */}
                <div style={{ position: "absolute", left: 26, right: 26, bottom: 26, height: 96, borderRadius: 48, background: "#262423", border: "1px solid #3a3734",
                  display: "flex", alignItems: "center", padding: "0 18px 0 30px", gap: 16 }}>
                  <div style={{ flex: 1, fontSize: 25, color: digitando ? "#F2EEE6" : "#6f6a62", whiteSpace: "nowrap", overflow: "hidden", direction: "rtl", textAlign: "left" }}>
                    <bdi>{digitando || "Pergunte qualquer coisa"}{digitando && cursorPisca ? <span style={{ color: C.ouro }}>|</span> : null}</bdi>
                  </div>
                  <div style={{ width: 62, height: 62, borderRadius: 31, background: digitando ? C.ouro : "#3a3734", display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 30, color: C.carvao, transform: `scale(${t > cmd.envia - 0.15 && t < cmd.envia + 0.1 ? 0.85 : 1})` }}>↑</div>
                </div>
              </div>
            </div>
          </div>
        ) : null}

        {/* rótulo do comando e legenda, trocando a cada comando */}
        {t >= 4.3 && t < SAIJ + 0.3
          ? COMANDOS.map((c, i) => {
              const entra = mola(t, fps, c.digita - 0.3, 14, 150);
              const sai = i < 2 ? entre(t, COMANDOS[i + 1].digita - 0.5, COMANDOS[i + 1].digita - 0.2) : entre(t, SAIJ, SAIJ + 0.3);
              if (entra <= 0.01 || sai >= 1) return null;
              return (
                <React.Fragment key={i}>
                  <div style={{ position: "absolute", left: JX, top: 330 - sai * 60, opacity: 1 - sai }}>
                    <Pilula x={0} y={0} k={entra} texto={`${c.rotulo[0]} · ${c.rotulo[1]}`} tipo="ouro" tam={32} />
                  </div>
                  <div style={{ opacity: 1 - sai }}>
                    <CardLegenda x={JX} y={1370} w={JW} k={mola(t, fps, c.resposta + 0.35)}>
                      <div style={{ position: "relative", height: 70 }}>
                        <Cinetico t={t} fps={fps} texto={c.legenda} inicio={c.resposta + 0.35} x={0} y={0} largura={870} tamanho={44} porPalavra={0.1} />
                      </div>
                    </CardLegenda>
                  </div>
                </React.Fragment>
              );
            })
          : null}

        {/* ===== ponte com o CRM ===== */}
        {t >= PONTE && t < CTA + 0.1 ? (
          <div style={{ transform: `translateY(${-entre(t, CTA - 0.4, CTA, Easing.in(Easing.cubic)) * 1300}px)`, filter: `blur(${Math.sin(entre(t, CTA - 0.4, CTA) * Math.PI) * 8}px)` }}>
            <Cinetico t={t} fps={fps} texto="Agora imagina isso no *WhatsApp* *da* *equipe* toda." inicio={PONTE + 0.1} y={760} tamanho={78} porPalavra={0.11} />
            <Bloco x={190} y={1150} tam={180} k={mola(t, fps, PONTE + 1.2)}><MarcaCiello largura={124} /></Bloco>
            <Pilula x={320} y={1112} k={mola(t, fps, PONTE + 1.5)} texto="é o CIELLO CRM" tam={40} tipo="ok" />
          </div>
        ) : null}

        {/* ===== CTA: salvar ===== */}
        {t >= CTA ? (
          <div style={{ transform: `translateY(${(1 - mola(t, fps, CTA - 0.1, 16, 110)) * 900}px)` }}>
            {(() => {
              const k = mola(t, fps, CTA, 12, 140);
              const enche = entre(t, CTA + 0.7, CTA + 1.0);
              const pop = 1 + Math.sin(entre(t, CTA + 0.7, CTA + 1.1) * Math.PI) * 0.18;
              return (
                <div style={{ position: "absolute", left: 80, top: 690, transform: `scale(${k * pop})`, transformOrigin: "60px 80px" }}>
                  <svg width={120} height={160} viewBox="0 0 120 160">
                    <path d="M14 10h92v138l-46-34-46 34z" fill={mixCor("#EDE7DA", C.ouro, enche)} stroke={C.carvao} strokeWidth={8} strokeLinejoin="round" />
                  </svg>
                </div>
              );
            })()}
            <Cinetico t={t} fps={fps} texto="Salva" inicio={CTA + 0.2} x={230} y={700} tamanho={150} peso={900} />
            <Cinetico t={t} fps={fps} texto="pra *usar* *hoje* na sua loja." inicio={CTA + 0.55} y={900} tamanho={62} porPalavra={0.1} />
            <Pilula x={80} y={1060} k={mola(t, fps, CTA + 1.6, 12, 160)} texto="e comenta COMANDOS: te mando os 3 por escrito" tam={34} tipo="ouro" />
            <div style={{ position: "absolute", left: 80, top: 1170, fontFamily: F.ui, fontSize: 28, color: TXT.leve, opacity: mola(t, fps, CTA + 2.2) }}>
              @ciellotec · tecnologia que eleva
            </div>
          </div>
        ) : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
