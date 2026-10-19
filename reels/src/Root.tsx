import React from "react";
import { Composition } from "remotion";
import { VendedorIA, VENDEDOR_TIMES } from "./VendedorIA";
import "./theme";
import { IvaSheet } from "./IvaSheet";
import { TesteIdeia, TESTE_TIMES } from "./TesteIdeia";
import { TextoIA, TEXTO_TIMES } from "./TextoIA";
import { CloneReel, MontagemClone, calcularClone } from "./CloneReel";
import exemploClone from "./montagens/exemplo-clone.json";

export const Root: React.FC = () => (
  <>
    <Composition id="VendedorIA" component={VendedorIA} durationInFrames={Math.round(VENDEDOR_TIMES.total * 30)} fps={30} width={1080} height={1920} />
    <Composition id="TesteIdeia" component={TesteIdeia} durationInFrames={Math.round(TESTE_TIMES.total * 30)} fps={30} width={1080} height={1920} />
    <Composition id="TextoIA" component={TextoIA} durationInFrames={Math.round(TEXTO_TIMES.total * 30)} fps={30} width={1080} height={1920} />
    {/* Montagem com clipes do clone digital; outra montagem entra por --props=arquivo.json no render.mjs */}
    <Composition id="CloneReel" component={CloneReel} defaultProps={exemploClone as MontagemClone} calculateMetadata={calcularClone} durationInFrames={1} fps={30} width={1080} height={1920} />
    <Composition id="IvaSheet" component={IvaSheet} durationInFrames={60} fps={30} width={1600} height={1100} />
  </>
);
