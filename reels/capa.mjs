// Gera a capa de um reel a partir do roteiro (cena "hook") ou de um JSON de capa.
// Uso: node capa.mjs ../roteiros/2026-10-28-post.json ../midia/capas/2026-10-28-post.jpg [--tema=creme] [--selo="3 TESTES"]
//      node capa.mjs capa.json saida.jpg        (JSON já no formato DadosCapa de src/Capa.tsx)
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import path from "node:path";
import fs from "node:fs";

const [entrada, saida] = process.argv.slice(2).filter((a) => !a.startsWith("--"));
if (!entrada || !saida) {
  console.error("uso: node capa.mjs <roteiro.json|capa.json> <saida.jpg|png> [--tema=carvao|creme] [--selo=...] [--iva=happy|think|surprise|idle|nenhuma] [--foto=clone/x.jpg]");
  process.exit(1);
}
const opt = Object.fromEntries(process.argv.filter((a) => a.startsWith("--")).map((a) => a.slice(2).split(/=(.*)/s).slice(0, 2)));

const dados = JSON.parse(fs.readFileSync(entrada, "utf8"));
let props;
if (dados.scenes) {
  const hook = dados.scenes.find((s) => s.type === "hook") ?? dados.scenes[0];
  props = { tag: hook.tag, linhas: hook.lines, apoio: hook.kicker, iva: hook.iva ?? "happy", ...(dados.capa ?? {}) };
} else {
  props = dados;
}
if (!props.linhas?.length) {
  console.error("O roteiro precisa de uma cena 'hook' com 'lines' (ou um bloco 'capa' com 'linhas').");
  process.exit(1);
}
// a composição mistura estas props com as de exemplo do Root: zera tudo que não veio para não herdar o exemplo
let marca = "";
try { marca = JSON.parse(fs.readFileSync(path.join(import.meta.dirname, "..", "comercial", "empresa.json"), "utf8")).nome || ""; } catch {}
props = { tema: "carvao", tag: null, apoio: null, selo: null, foto: null, iva: "happy", marca, ...props };
if (opt.tema) props.tema = opt.tema;
if (opt.selo) props.selo = opt.selo;
if (opt.foto) props.foto = opt.foto;
if (opt.iva) props.iva = opt.iva === "nenhuma" ? null : opt.iva;

const browserExecutable = process.env.REMOTION_CHROME || [
  "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
  "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
].find((p) => fs.existsSync(p));

const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts") });
const composition = await selectComposition({ serveUrl, id: "Capa", inputProps: props, browserExecutable });
fs.mkdirSync(path.dirname(path.resolve(saida)), { recursive: true });
await renderStill({
  composition, serveUrl, inputProps: props, frame: 0, output: saida, browserExecutable,
  imageFormat: saida.endsWith(".png") ? "png" : "jpeg", jpegQuality: 92,
});
console.log("ok", saida);
