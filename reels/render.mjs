// Renderiza uma composição do Remotion usando o Chromium já instalado na máquina.
// Uso: node render.mjs <Composicao> <saida.mp4> [--frames=0,30,60 --stills=pasta] [--props=montagem.json]
import { bundle } from "@remotion/bundler";
import { renderMedia, renderStill, selectComposition } from "@remotion/renderer";
import path from "node:path";
import fs from "node:fs";

const [id, out] = process.argv.slice(2);
const framesArg = process.argv.find((a) => a.startsWith("--frames="));
const stillsArg = process.argv.find((a) => a.startsWith("--stills="));
const propsArg = process.argv.find((a) => a.startsWith("--props="));
const inputProps = propsArg ? JSON.parse(fs.readFileSync(propsArg.split("=")[1], "utf8")) : undefined;
const browserExecutable = process.env.REMOTION_CHROME || [
  "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
  "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
].find((p) => fs.existsSync(p));

const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts") });
const composition = await selectComposition({ serveUrl, id, browserExecutable, inputProps });

if (framesArg) {
  const dir = stillsArg ? stillsArg.split("=")[1] : "stills";
  fs.mkdirSync(dir, { recursive: true });
  for (const f of framesArg.split("=")[1].split(",").map(Number)) {
    await renderStill({ composition, serveUrl, inputProps, frame: f, output: path.join(dir, `${id}-${f}.png`), browserExecutable });
  }
  console.log("stills ok");
} else {
  await renderMedia({
    composition, serveUrl, inputProps, codec: "h264", outputLocation: out, browserExecutable,
    concurrency: 2, crf: 18, pixelFormat: "yuv420p",
    onProgress: ({ progress }) => { if (Math.round(progress * 100) % 10 === 0) process.stdout.write(`\r${Math.round(progress * 100)}%`); },
  });
  console.log("\nok", out);
}
