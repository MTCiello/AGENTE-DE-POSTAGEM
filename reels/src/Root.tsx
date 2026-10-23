import React from "react";
import { Composition } from "remotion";
import "./theme";
import { IvaSheet } from "./IvaSheet";
import { CloneReel, MontagemClone, calcularClone } from "./CloneReel";
import exemploClone from "./montagens/exemplo-clone.json";
import { Capa, DadosCapa } from "./Capa";

const CAPA_EXEMPLO: DadosCapa = {
  tag: "IA pro seu negócio", linhas: [["5 comandos", "marfim"], ["do ChatGPT", "cinza"], ["que vendem", "ouro"]],
  apoio: "Salva pra usar hoje", selo: "Grátis", iva: "happy",
};

export const Root: React.FC = () => (
  <>
    {/* Montagem com clipes do clone digital; outra montagem entra por --props=arquivo.json no render.mjs */}
    <Composition id="CloneReel" component={CloneReel} defaultProps={exemploClone as MontagemClone} calculateMetadata={calcularClone} durationInFrames={1} fps={30} width={1080} height={1920} />
    <Composition id="Capa" component={Capa} defaultProps={CAPA_EXEMPLO} durationInFrames={1} fps={30} width={1080} height={1920} />
    <Composition id="IvaSheet" component={IvaSheet} durationInFrames={60} fps={30} width={1600} height={1100} />
  </>
);
