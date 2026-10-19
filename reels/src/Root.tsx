import React from "react";
import { Composition } from "remotion";
import { VendedorIA, VENDEDOR_TIMES } from "./VendedorIA";
import "./theme";

export const Root: React.FC = () => (
  <>
    <Composition id="VendedorIA" component={VendedorIA} durationInFrames={Math.round(VENDEDOR_TIMES.total * 30)} fps={30} width={1080} height={1920} />
  </>
);
