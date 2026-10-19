import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { Iva } from "./Iva";
export const IvaSheet: React.FC = () => {
  const frame = useCurrentFrame(); const { fps } = useVideoConfig();
  const moods: any[] = [["idle", false], ["idle", true], ["happy", false], ["think", false], ["surprise", false], ["idle", false]];
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 40%, #EEEAE0, #CFC8B8)", flexDirection: "row", flexWrap: "wrap", alignItems: "center", justifyContent: "center", gap: 30 }}>
      {moods.map(([m, tk], i) => <div key={i} style={{ width: 480 }}><Iva frame={frame + i * 7} fps={fps} size={460} mood={m} talking={tk} look={i === 5 ? [1, -0.4] : [0, 0]} /></div>)}
    </AbsoluteFill>
  );
};
