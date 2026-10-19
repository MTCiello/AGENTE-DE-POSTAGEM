/* Ciello OS: o escritório de agentes (pixel-agents) é o fundo da área de trabalho; barra de tarefas embaixo, apps no
   menu Iniciar e janelas que movem e redimensionam. Clicar num personagem do escritório abre a janela daquele agente.
   Os dados vêm do servidor local (central/escritorio/servidor.py); os botões só rodam as ações da lista dele. */
'use strict';
const TOKEN = window.CIELLO_TOKEN; delete window.CIELLO_TOKEN; // fica só aqui dentro, não em window

// ------------------------------------------------------------------ ícones (traço branco, 24x24)
const SVG = {
  escritorio: '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/><circle cx="9" cy="9" r="1.6"/><circle cx="15" cy="9" r="1.6"/><path d="M6.5 13.5c.6-1.3 1.5-2 2.5-2s1.9.7 2.5 2M12.5 13.5c.6-1.3 1.5-2 2.5-2s1.9.7 2.5 2"/>',
  sol: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  financeiro: '<path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 6-6"/><path d="M16 8h4v4"/>',
  comercial: '<path d="M3 4h18l-7 8v6l-4 2v-8z"/>',
  conteudo: '<rect x="3" y="3" width="18" height="18" rx="4"/><path d="M10 8.5v7l6-3.5z"/>',
  tendencias: '<path d="M12 22c4 0 7-2.7 7-6.7 0-4.2-3-6.3-4.3-9.3-.4 2.4-1.7 3.7-3 4.3 0-3-1.2-5.6-3.7-7.3.3 3.3-3 5.6-3 10.3C5 19.3 8 22 12 22z"/>',
  concorrentes: '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
  anuncios: '<path d="M3 11v2a2 2 0 0 0 2 2h1l4 4V5L6 9H5a2 2 0 0 0-2 2z"/><path d="M14 8a5 5 0 0 1 0 8M17 5a9 9 0 0 1 0 14"/>',
  equipe: '<circle cx="9" cy="8" r="3.2"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><circle cx="17" cy="9" r="2.5"/><path d="M16 14.2c2.9.3 5 2.6 5 5.8"/>',
  atividade: '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
  verificar: '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
  terminal: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 9l3 3-3 3M13 15h4"/>',
  agente: '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/>',
  pino: '<path d="M12 17v5M9 3h6l-1 6 3 3v2H7v-2l3-3z"/>',
  play: '<path d="M7 5v14l11-7z"/>',
  min: '<path d="M2 6h8"/>', max: '<rect x="2" y="2" width="8" height="8"/>', rest: '<rect x="2" y="4" width="6" height="6"/><path d="M4 4V2h6v6H8"/>', fechar: '<path d="M2 2l8 8M10 2l-8 8"/>',
};
const icone = (n, vb = 24) => `<svg viewBox="0 0 ${vb} ${vb}">${SVG[n] || SVG.agente}</svg>`;

// ------------------------------------------------------------------ apps
const APPS = {
  briefing: { titulo: 'Bom dia', icone: 'sol', cor: 'linear-gradient(135deg,#F7A35C,#E0722F)', w: 640, h: 660, render: renderBriefing },
  financeiro: { titulo: 'Financeiro', icone: 'financeiro', cor: 'linear-gradient(135deg,#3CC285,#1F8A4C)', w: 900, h: 680, render: renderFinanceiro },
  comercial: { titulo: 'Comercial', icone: 'comercial', cor: 'linear-gradient(135deg,#5E92E6,#2F5BA8)', w: 880, h: 660, render: renderComercial },
  conteudo: { titulo: 'Conteúdo e Instagram', icone: 'conteudo', cor: 'linear-gradient(135deg,#EC70A0,#C2416F)', w: 920, h: 680, render: renderConteudo },
  tendencias: { titulo: 'Tendências', icone: 'tendencias', cor: 'linear-gradient(135deg,#F48D5E,#D24E36)', w: 740, h: 640, render: (j) => renderRelatorio(j, 'tendencias') },
  concorrentes: { titulo: 'Concorrentes', icone: 'concorrentes', cor: 'linear-gradient(135deg,#4CC6D1,#1E8C99)', w: 740, h: 620, render: (j) => renderRelatorio(j, 'concorrentes') },
  anuncios: { titulo: 'Anúncios', icone: 'anuncios', cor: 'linear-gradient(135deg,#AE92EE,#6B4FBB)', w: 780, h: 540, render: renderAnuncios },
  equipe: { titulo: 'Equipe', icone: 'equipe', cor: 'linear-gradient(135deg,#7385AC,#3A4C70)', w: 860, h: 620, render: renderEquipe, cada: 4000 },
  atividade: { titulo: 'Atividade', icone: 'atividade', cor: 'linear-gradient(135deg,#7E8AA1,#4B566B)', w: 520, h: 580, render: renderAtividade, cada: 3000 },
  verificar: { titulo: 'Verificação', icone: 'verificar', cor: 'linear-gradient(135deg,#5BC0A0,#2D8C70)', acao: 'verificar' },
};
const MENU = ['briefing', 'financeiro', 'comercial', 'conteudo', 'tendencias', 'concorrentes', 'anuncios', 'equipe', 'atividade', 'verificar'];

const NOMES = { 'chefe-gabinete': 'Chefe de Gabinete', 'pesquisador-mercado': 'Pesquisador de Mercado', roteirista: 'Roteirista', 'produtor-video': 'Produtor de Vídeo',
  'produtor-imagem': 'Produtor de Imagem', postagem: 'Postagem', analista: 'Analista', 'gestor-anuncios': 'Gestor de Anúncios', sdr: 'SDR', closer: 'Closer',
  financeiro: 'Financeiro', 'caixa-entrada': 'Caixa de Entrada', 'sucesso-cliente': 'Sucesso do Cliente', sistema: 'Sistema', Mateus: 'Você' };
const CORES = { cyan: '#2FB7C4', blue: '#3B7BE0', green: '#2FA36B', orange: '#E07B39', pink: '#D9579A', purple: '#8E6BD8', red: '#D9533B', yellow: '#E0A81C' };
const COMANDOS = { 'chefe-gabinete': ['/bom-dia', '/sexta'], financeiro: ['/bom-dia', '/sexta'], 'caixa-entrada': ['/bom-dia'], 'sucesso-cliente': ['/bom-dia'],
  sdr: ['/comercial'], closer: ['/comercial'], 'pesquisador-mercado': ['/semana', '/segunda', '/sexta'], roteirista: ['/semana'], 'produtor-video': ['/semana'],
  'produtor-imagem': ['/semana'], postagem: ['/semana'], analista: ['/segunda'], 'gestor-anuncios': ['/segunda'] };
const ROTULO_ESTADO = { trabalhando: 'trabalhando', pensando: 'pensando', esperando: 'precisa de você', pronto: 'pronto', erro: 'erro', parado: 'livre' };

// ------------------------------------------------------------------ utilidades
const $ = (s, el = document) => el.querySelector(s);
const esc = (t) => String(t ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const brl = (n) => (n ?? 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
const num = (n) => (n ?? 0).toLocaleString('pt-BR');
const nome = (a) => NOMES[a] || a;
const ddmm = (iso) => iso ? `${iso.slice(8, 10)}/${iso.slice(5, 7)}` : '';
const semSelecao = () => { try { window.getSelection().removeAllRanges(); } catch { /* nada selecionado */ } };
const area = () => ({ w: $('#mesa').clientWidth, h: $('#mesa').clientHeight });
let offline = false;

async function api(caminho, corpo) {
  const op = corpo ? { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Ciello-Token': TOKEN }, body: JSON.stringify(corpo) } : {};
  try {
    const r = await fetch(caminho, op);
    if (offline) { offline = false; aviso({ titulo: 'Conectado de novo', texto: 'O servidor do Ciello OS voltou.', cor: '#1F8A4C' }); }
    return await r.json();
  } catch (e) {
    if (!offline) { offline = true; aviso({ titulo: 'Servidor desligado', texto: 'Abra o Ciello.cmd de novo para reconectar.', cor: '#C8442F' }); }
    throw e;
  }
}

function md(txt) {
  const inline = (s) => esc(s).replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>')
    .replace(/(^|[\s(])_([^_]+)_(?=[\s).,;:!?]|$)/g, '$1<i>$2</i>')
    .replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  const out = []; let lista = null; let codigo = false; let tabela = [];
  const fechar = () => { if (lista) { out.push(`</${lista}>`); lista = null; } };
  const fecharTabela = () => {
    if (!tabela.length) return;
    const linhas = tabela.filter((l) => !/^\|\s*-/.test(l)).map((l) => l.replace(/^\||\|$/g, '').split('|').map((c) => inline(c.trim())));
    out.push('<table><tr>' + linhas[0].map((c) => `<th>${c}</th>`).join('') + '</tr>' + linhas.slice(1).map((l) => '<tr>' + l.map((c) => `<td>${c}</td>`).join('') + '</tr>').join('') + '</table>');
    tabela = [];
  };
  for (const l of String(txt || '').split('\n')) {
    if (l.startsWith('```')) { fechar(); out.push(codigo ? '</pre>' : '<pre class="console">'); codigo = !codigo; continue; }
    if (codigo) { out.push(esc(l) + '\n'); continue; }
    if (l.trim().startsWith('|')) { fechar(); tabela.push(l.trim()); continue; }
    fecharTabela();
    let m;
    if ((m = l.match(/^(#{1,3})\s+(.*)/))) { fechar(); out.push(`<h${m[1].length}>${inline(m[2])}</h${m[1].length}>`); }
    else if ((m = l.match(/^\s*[-*]\s+(.*)/))) { if (lista !== 'ul') { fechar(); out.push('<ul>'); lista = 'ul'; } out.push(`<li>${inline(m[1])}</li>`); }
    else if ((m = l.match(/^\s*\d+\.\s+(.*)/))) { if (lista !== 'ol') { fechar(); out.push('<ol>'); lista = 'ol'; } out.push(`<li>${inline(m[1])}</li>`); }
    else if ((m = l.match(/^>\s?(.*)/))) { fechar(); out.push(`<blockquote>${inline(m[1])}</blockquote>`); }
    else if (l.trim()) { fechar(); out.push(`<p>${inline(l)}</p>`); }
    else fechar();
  }
  fechar(); fecharTabela();
  return out.join('');
}

// personagem em pixel, na cor do agente (combina com o pixel-agents)
const MOLDE = ['....HHHH....', '...HHHHHH...', '...HSSSSH...', '...SESSES...', '...SSSSSS...', '....SSSS....', '..CCCCCCCC..',
  '.CCCCCCCCCC.', '.SCCCCCCCCS.', '.SCCCCCCCCS.', '..CCCCCCCC..', '..PPP..PPP..', '..PPP..PPP..', '..BB....BB..'];
const CABELOS = ['#2B1D14', '#5A3A22', '#1F1F24', '#8A5A2B', '#C9A15B'];
const PELES = ['#F1C7A5', '#D9A47E', '#B07850', '#8A5A3C'];
function sprite(agente, tam = 28) {
  let h = 0; for (const c of agente) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  const cor = { H: CABELOS[h % 5], S: PELES[(h >> 3) % 4], E: '#1B1B22', C: CORES[(equipeCache.find((a) => a.nome === agente) || {}).cor] || '#8C877C', P: '#3A4256', B: '#1B1B22' };
  let r = '';
  MOLDE.forEach((linha, y) => [...linha].forEach((ch, x) => { if (cor[ch]) r += `<rect x="${x}" y="${y}" width="1.02" height="1.02" fill="${cor[ch]}"/>`; }));
  return `<svg class="sprite" width="${tam}" height="${tam * 14 / 12}" viewBox="0 0 12 14" shape-rendering="crispEdges">${r}</svg>`;
}
const papel = (d) => { const t = String(d || '').split(': ')[0].split(/\.\s|,\s|\s\(/)[0]; return t.length > 72 ? `${t.slice(0, 70)}…` : t; };
const chipEstado = (e) => `<span class="chip ${esc(e || 'parado')}"><i></i>${esc(ROTULO_ESTADO[e] || e || 'livre')}</span>`;

// ------------------------------------------------------------------ estado salvo (posição das janelas, o que estava aberto)
const SALVO = (() => { try { return JSON.parse(localStorage.getItem('ciello.os')) || {}; } catch { return {}; } })();
SALVO.geo = SALVO.geo || {}; SALVO.abertas = SALVO.abertas || []; if (SALVO.auto === undefined) SALVO.auto = true;
const salvar = () => { try { SALVO.abertas = [...janelas.keys()].filter((k) => !k.startsWith('exec:')); localStorage.setItem('ciello.os', JSON.stringify(SALVO)); } catch { /* modo privado */ } };

// ------------------------------------------------------------------ gerenciador de janelas
const janelas = new Map();
let zTopo = 10; let ativa = null;
const MIN_W = 340; const MIN_H = 220;

function definicao(chave) {
  if (APPS[chave]) return APPS[chave];
  if (chave.startsWith('agente:')) {
    const a = chave.slice(7);
    return { titulo: nome(a), icone: 'agente', cor: CORES[(equipeCache.find((x) => x.nome === a) || {}).cor] || '#6E7FA3', w: 560, h: 600, render: renderAgente, cada: 2500, agente: a };
  }
  if (chave.startsWith('exec:')) return { titulo: 'Executando…', icone: 'terminal', cor: 'linear-gradient(135deg,#3A4256,#12151C)', w: 700, h: 460, render: renderExecucao, estatico: true };
  return null;
}

function abrir(chave, dados = {}) {
  const def = definicao(chave);
  if (!def) return null;
  if (def.acao) { rodarAcao(def.acao); return null; }
  fecharMenus();
  if (janelas.has(chave)) { const j = janelas.get(chave); restaurar(j); focar(j); return j; }
  const { w: W, h: H } = area();
  const n = janelas.size;
  const g = SALVO.geo[chave] || { w: Math.min(def.w, W - 40), h: Math.min(def.h, H - 30), x: Math.max(110, Math.min(W - def.w - 20, 140 + (n * 34) % 260)), y: 18 + (n * 30) % 150 };
  const el = document.createElement('section');
  el.className = 'janela';
  el.innerHTML = `<header class="barra"><span class="ic" style="background:${def.cor}">${icone(def.icone)}</span><span class="titulo">${esc(def.titulo)}</span>
    <div class="botoes"><button class="minimizar" title="Minimizar">${icone('min', 12)}</button><button class="maximizar" title="Maximizar">${icone('max', 12)}</button><button class="fechar" title="Fechar">${icone('fechar', 12)}</button></div></header>
    <div class="conteudo"></div>` + ['n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw'].map((d) => `<div class="borda ${d}" data-d="${d}"></div>`).join('');
  $('#janelas').appendChild(el);
  const j = { chave, def, el, corpo: $('.conteudo', el), dados, min: false, max: false, prev: null, timer: null };
  janelas.set(chave, j);
  posicionar(j, g);
  if (g.max) maximizar(j);
  ligarJanela(j);
  focar(j);
  desenhar(j);
  if (!def.estatico) j.timer = setInterval(() => { if (!j.min) (def.atualizar || desenhar)(j, true); }, def.cada || 20000);
  barraTarefas(); salvar();
  return j;
}

async function desenhar(j, silencioso) {
  const rolagem = j.corpo.scrollTop;
  if (!silencioso) j.corpo.innerHTML = '<div class="pagina"><p class="sub">Carregando…</p></div>';
  try { await j.def.render(j); } catch (e) { if (!silencioso) j.corpo.innerHTML = `<div class="pagina"><div class="vazio">Não consegui carregar: ${esc(e.message || e)}</div></div>`; }
  j.corpo.scrollTop = rolagem;
}

function posicionar(j, g) {
  const { w: W, h: H } = area();
  const w = Math.max(MIN_W, Math.min(g.w, W)); const h = Math.max(MIN_H, Math.min(g.h, H));
  Object.assign(j.el.style, { left: `${Math.min(Math.max(g.x, -w + 120), W - 120)}px`, top: `${Math.min(Math.max(g.y, 0), H - 40)}px`, width: `${w}px`, height: `${h}px` });
}
const geo = (j) => ({ x: j.el.offsetLeft, y: j.el.offsetTop, w: j.el.offsetWidth, h: j.el.offsetHeight });
function guardarGeo(j) { SALVO.geo[j.chave] = j.max ? { ...(j.prev || geo(j)), max: true } : geo(j); salvar(); }

function focar(j) {
  if (ativa === j && j.el.style.zIndex) return;
  j.el.style.zIndex = ++zTopo;
  janelas.forEach((x) => x.el.classList.toggle('ativa', x === j));
  ativa = j; barraTarefas();
}
function focarTopo() {
  const vis = [...janelas.values()].filter((x) => !x.min).sort((a, b) => b.el.style.zIndex - a.el.style.zIndex);
  ativa = null; janelas.forEach((x) => x.el.classList.remove('ativa'));
  if (vis[0]) focar(vis[0]); else barraTarefas();
}
function minimizar(j) { j.min = true; j.el.classList.add('min'); focarTopo(); }
function restaurar(j) { if (j.min) { j.min = false; j.el.classList.remove('min'); } }
function maximizar(j) {
  if (!j.max) j.prev = geo(j);
  j.max = true; j.el.classList.add('max');
  Object.assign(j.el.style, { left: '0px', top: '0px', width: '100%', height: '100%' });
  $('.maximizar', j.el).innerHTML = icone('rest', 12); $('.maximizar', j.el).title = 'Restaurar';
}
function desmaximizar(j) {
  j.max = false; j.el.classList.remove('max');
  posicionar(j, j.prev || { x: 120, y: 30, w: j.def.w, h: j.def.h });
  $('.maximizar', j.el).innerHTML = icone('max', 12); $('.maximizar', j.el).title = 'Maximizar';
}
function alternarMax(j) { j.max ? desmaximizar(j) : maximizar(j); guardarGeo(j); }
function fechar(j) {
  clearInterval(j.timer); clearInterval(j.timerExec);
  j.el.classList.add('fechando');
  setTimeout(() => j.el.remove(), 120);
  janelas.delete(j.chave);
  if (ativa === j) focarTopo(); else barraTarefas();
  salvar();
}

function zonaEncaixe(ev) {
  const { w: W } = area();
  if (ev.clientY <= 4) return 'max';
  if (ev.clientX <= 4) return 'esq';
  if (ev.clientX >= W - 4) return 'dir';
  return null;
}
function mostrarEncaixe(zona) {
  const p = $('#encaixe'); const { w: W, h: H } = area();
  if (!zona) { p.hidden = true; return; }
  const r = { max: [6, 6, W - 12, H - 12], esq: [6, 6, W / 2 - 9, H - 12], dir: [W / 2 + 3, 6, W / 2 - 9, H - 12] }[zona];
  Object.assign(p.style, { left: `${r[0]}px`, top: `${r[1]}px`, width: `${r[2]}px`, height: `${r[3]}px` }); p.hidden = false;
}
function encaixar(j, zona) {
  if (zona === 'max') return maximizar(j);
  const { w: W, h: H } = area();
  j.prev = j.prev || geo(j);
  posicionar(j, { x: zona === 'esq' ? 0 : W / 2, y: 0, w: W / 2, h: H });
}

function ligarJanela(j) {
  const { el } = j; const barra = $('.barra', el);
  el.addEventListener('pointerdown', () => focar(j), true);
  $('.minimizar', el).onclick = () => minimizar(j);
  $('.maximizar', el).onclick = () => alternarMax(j);
  $('.fechar', el).onclick = () => fechar(j);
  barra.addEventListener('dblclick', (e) => { if (!e.target.closest('button')) alternarMax(j); });

  barra.addEventListener('pointerdown', (e) => {
    if (e.button !== 0 || e.target.closest('button')) return;
    e.preventDefault(); semSelecao(); document.body.classList.add('arrastando'); // sem seleção de texto enquanto arrasta
    const r = el.getBoundingClientRect(); const mesa = $('#mesa').getBoundingClientRect();
    let ox = e.clientX - r.left; let oy = e.clientY - r.top; const sx = e.clientX; const sy = e.clientY; let andou = false; let zona = null;
    barra.setPointerCapture(e.pointerId);
    const mover = (ev) => {
      if (!andou && Math.hypot(ev.clientX - sx, ev.clientY - sy) < 4) return;
      if (!andou) {
        andou = true;
        if (j.max) { const prop = ox / r.width; desmaximizar(j); ox = prop * el.offsetWidth; oy = 20; }
      }
      const { w: W, h: H } = area();
      el.style.left = `${Math.min(Math.max(ev.clientX - mesa.left - ox, -el.offsetWidth + 120), W - 120)}px`;
      el.style.top = `${Math.min(Math.max(ev.clientY - mesa.top - oy, 0), H - 40)}px`;
      zona = zonaEncaixe(ev); mostrarEncaixe(zona);
    };
    const soltar = () => {
      barra.removeEventListener('pointermove', mover); barra.removeEventListener('pointerup', soltar); barra.removeEventListener('pointercancel', soltar);
      document.body.classList.remove('arrastando'); mostrarEncaixe(null); semSelecao();
      if (andou) { if (zona) encaixar(j, zona); else j.prev = null; guardarGeo(j); }
    };
    barra.addEventListener('pointermove', mover); barra.addEventListener('pointerup', soltar); barra.addEventListener('pointercancel', soltar);
  });

  el.querySelectorAll('.borda').forEach((b) => b.addEventListener('pointerdown', (e) => {
    if (e.button !== 0) return;
    e.preventDefault(); e.stopPropagation(); focar(j); semSelecao();
    const d = b.dataset.d; const r0 = geo(j); const sx = e.clientX; const sy = e.clientY;
    b.setPointerCapture(e.pointerId);
    document.body.classList.add('arrastando'); document.body.style.cursor = getComputedStyle(b).cursor;
    const mover = (ev) => {
      const dx = ev.clientX - sx; const dy = ev.clientY - sy; let { x, y, w, h } = r0;
      if (d.includes('e')) w = Math.max(MIN_W, r0.w + dx);
      if (d.includes('s')) h = Math.max(MIN_H, Math.min(r0.h + dy, area().h - r0.y));
      if (d.includes('w')) { w = Math.max(MIN_W, r0.w - dx); x = r0.x + r0.w - w; }
      if (d.includes('n')) { h = Math.max(MIN_H, r0.h - dy); y = r0.y + r0.h - h; if (y < 0) { h += y; y = 0; } }
      Object.assign(el.style, { left: `${x}px`, top: `${y}px`, width: `${w}px`, height: `${h}px` });
    };
    const soltar = () => {
      b.removeEventListener('pointermove', mover); b.removeEventListener('pointerup', soltar); b.removeEventListener('pointercancel', soltar);
      document.body.classList.remove('arrastando'); document.body.style.cursor = ''; semSelecao(); guardarGeo(j);
    };
    b.addEventListener('pointermove', mover); b.addEventListener('pointerup', soltar); b.addEventListener('pointercancel', soltar);
  }));

  // botões dentro das janelas: data-acao roda uma ação da lista do servidor, data-abrir abre outra janela
  el.addEventListener('click', (e) => {
    const a = e.target.closest('[data-acao]'); if (a) return rodarAcao(a.dataset.acao);
    const o = e.target.closest('[data-abrir]'); if (o) abrir(o.dataset.abrir);
  });
}

// clicar no escritório (o fundo) fecha os menus, como clicar na área de trabalho do Windows
window.addEventListener('blur', () => setTimeout(() => { if (document.activeElement && document.activeElement.id === 'escritorio') fecharMenus(); }));

function organizar() {
  let i = 0; const { w: W, h: H } = area();
  [...janelas.values()].filter((j) => !j.min).sort((a, b) => a.el.style.zIndex - b.el.style.zIndex).forEach((j) => {
    if (j.max) desmaximizar(j);
    posicionar(j, { x: 120 + i * 36, y: 16 + i * 32, w: Math.min(j.def.w, W - 160), h: Math.min(j.def.h, H - 60) }); guardarGeo(j); focar(j); i++;
  });
}

// ------------------------------------------------------------------ barra de tarefas, menu iniciar, avisos
const tile = (def, cls = 'tile') => `<span class="${cls}" style="background:${def.cor}">${icone(def.icone)}</span>`;

function barraTarefas() {
  const vazia = ![...janelas.values()].some((j) => !j.min);
  $('#fixados').innerHTML = `<button class="fixado ${vazia ? 'ativa' : ''}" id="mostrar-escritorio" title="Mostrar o escritório (minimiza as janelas)">${tile({ cor: 'linear-gradient(135deg,#F1C95A,#D99A0B)', icone: 'escritorio' })}</button>`;
  $('#abertas').innerHTML = [...janelas.values()].map((j) =>
    `<button class="aberta ${ativa === j && !j.min ? 'ativa' : ''}" data-chave="${esc(j.chave)}" title="${esc(j.def.titulo)}">${tile(j.def)}<span>${esc(j.def.titulo)}</span></button>`).join('');
}
function cliqueTarefa(e) {
  const b = e.target.closest('[data-chave]'); if (!b) return;
  const j = janelas.get(b.dataset.chave);
  if (!j) return abrir(b.dataset.chave);
  if (j.min) { restaurar(j); focar(j); } else if (ativa === j) minimizar(j); else focar(j);
}
$('#abertas').addEventListener('click', cliqueTarefa);
$('#mesa').addEventListener('pointerdown', (e) => { if (!e.target.closest('.janela')) fecharMenus(); });

// "Mostrar o escritório": minimiza tudo; clicar de novo traz as mesmas janelas de volta (como no Windows)
let escondidas = [];
function mostrarEscritorio() {
  fecharMenus();
  const vis = [...janelas.values()].filter((j) => !j.min);
  if (vis.length) { escondidas = vis.map((j) => j.chave); vis.forEach((j) => { j.min = true; j.el.classList.add('min'); }); focarTopo(); return; }
  escondidas.forEach((k) => { const j = janelas.get(k); if (j) { restaurar(j); focar(j); } }); escondidas = [];
}
$('#fixados').addEventListener('click', mostrarEscritorio);

function desenharMenu(filtro = '') {
  const f = filtro.toLowerCase();
  $('#menu-apps').innerHTML = MENU.filter((k) => APPS[k].titulo.toLowerCase().includes(f)).map((k) =>
    `<button class="item-app" data-chave="${k}">${tile(APPS[k])}<span>${esc(APPS[k].titulo)}</span></button>`).join('');
  $('#menu-equipe').innerHTML = equipeCache.filter((a) => nome(a.nome).toLowerCase().includes(f)).map((a) =>
    `<button class="item-agente" data-chave="agente:${esc(a.nome)}">${sprite(a.nome, 22)}<div><b>${esc(nome(a.nome))}</b><small>${esc(ROTULO_ESTADO[estadoAgente(a.nome).estado] || 'livre')}</small></div></button>`).join('');
}
function fecharMenus() { $('#menu').hidden = true; $('#central').hidden = true; $('#iniciar').classList.remove('on'); }
$('#iniciar').onclick = (e) => { e.stopPropagation(); const abrirMenu = $('#menu').hidden; fecharMenus(); if (abrirMenu) { desenharMenu(); $('#menu').hidden = false; $('#iniciar').classList.add('on'); $('#busca').value = ''; $('#busca').focus(); } };
$('#busca').oninput = (e) => desenharMenu(e.target.value);
$('#menu').addEventListener('click', (e) => { const b = e.target.closest('[data-chave]'); if (b) abrir(b.dataset.chave); });
$('#auto').checked = SALVO.auto; $('#auto').onchange = (e) => { SALVO.auto = e.target.checked; salvar(); };
$('#organizar').onclick = () => { fecharMenus(); organizar(); };
$('#ver-escritorio').onclick = () => { fecharMenus(); if ([...janelas.values()].some((j) => !j.min)) mostrarEscritorio(); };
$('#tela-cheia').onclick = () => { fecharMenus(); document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen(); };
$('#sino').onclick = (e) => { e.stopPropagation(); const ab = $('#central').hidden; fecharMenus(); if (ab) { desenharCentral(); $('#central').hidden = false; naoLidas = 0; contarNaoLidas(); } };
$('#trabalhando').onclick = () => abrir('equipe');
$('#central').addEventListener('click', (e) => { const n = e.target.closest('[data-chave]'); if (n) abrir(n.dataset.chave); });
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') fecharMenus();
  if (e.key === 'Meta' || (e.ctrlKey && e.key === 'Escape')) $('#iniciar').click();
});
document.addEventListener('click', (e) => { if (!e.target.closest('.menu, .central, #iniciar, #sino')) fecharMenus(); });

const notificacoes = []; let naoLidas = 0;
function contarNaoLidas() { const b = $('#sino em'); b.hidden = !naoLidas; b.textContent = naoLidas; }
function desenharCentral() {
  $('#central-lista').innerHTML = notificacoes.map((n) => `<div class="notif" ${n.chave ? `data-chave="${esc(n.chave)}"` : ''}>${n.agente ? sprite(n.agente, 22) : ''}<div><b>${esc(n.titulo)}</b><small>${esc(n.texto)} · ${esc(n.hora)}</small></div></div>`).join('')
    || '<p class="sub">Nada por aqui ainda.</p>';
}
function aviso({ titulo, texto = '', agente = null, chave = null, cor = '#E0A81C' }) {
  notificacoes.unshift({ titulo, texto, agente, chave, hora: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) });
  notificacoes.length = Math.min(notificacoes.length, 40); naoLidas++; contarNaoLidas();
  const el = document.createElement('div'); el.className = 'aviso'; el.style.borderLeftColor = cor;
  el.innerHTML = `${agente ? sprite(agente, 26) : ''}<div><b>${esc(titulo)}</b><small>${esc(texto)}</small></div>`;
  el.onclick = () => { if (chave) abrir(chave); el.remove(); };
  $('#avisos').appendChild(el);
  setTimeout(() => { el.classList.add('sai'); setTimeout(() => el.remove(), 260); }, 6500);
}

function relogio() {
  const d = new Date();
  $('#relogio b').textContent = d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  $('#relogio small').textContent = d.toLocaleDateString('pt-BR');
}

// ------------------------------------------------------------------ agentes ao vivo
let equipeCache = []; let estadoCache = { agentes: {}, eventos: [] };
const vistos = new Set(); let primeiraLeitura = true; const suprimir = {};
const estadoAgente = (n) => estadoCache.agentes[n] || { estado: 'parado', tarefa: '' };

async function puxarEquipe() { try { equipeCache = await api('/api/equipe'); } catch { /* tenta de novo */ } }
async function puxarEstado() {
  try { estadoCache = await api('/api/estado'); } catch { return; }
  const ativos = Object.values(estadoCache.agentes).filter((a) => a.estado === 'trabalhando').length;
  $('#trabalhando').classList.toggle('on', ativos > 0);
  $('#trabalhando span').textContent = ativos ? `${ativos} trabalhando` : 'equipe livre';
  for (const e of [...estadoCache.eventos].reverse()) {
    const k = `${e.ts}|${e.agente}|${e.estado}|${e.tarefa}`;
    if (vistos.has(k)) continue;
    vistos.add(k);
    if (primeiraLeitura) continue;
    const local = suprimir[e.agente] && Date.now() - suprimir[e.agente] < 15000;
    const chave = `agente:${e.agente}`;
    if (e.estado === 'trabalhando' && !local) {
      aviso({ titulo: `${nome(e.agente)} começou`, texto: e.tarefa, agente: e.agente, chave, cor: '#2DBE6C' });
      if (SALVO.auto && definicao(chave)) abrir(chave);
    } else if (e.estado === 'esperando') aviso({ titulo: `${nome(e.agente)} precisa de você`, texto: e.tarefa, agente: e.agente, chave, cor: '#E0A81C' });
    else if (e.estado === 'erro') aviso({ titulo: `${nome(e.agente)}: erro`, texto: e.tarefa, agente: e.agente, chave, cor: '#C8442F' });
    else if (e.estado === 'pronto' && !local) aviso({ titulo: `${nome(e.agente)} terminou`, texto: e.tarefa, agente: e.agente, chave, cor: '#3A5582' });
  }
  primeiraLeitura = false;
}

async function rodarAcao(acao) {
  fecharMenus();
  try {
    const ex = await api('/api/rodar', { acao });
    if (ex.erro) return aviso({ titulo: 'Não rodou', texto: ex.erro, cor: '#C8442F' });
    suprimir[ex.agente] = Date.now();
    abrir(`exec:${ex.id}`, ex);
  } catch { /* o aviso de servidor desligado já apareceu */ }
}

// ------------------------------------------------------------------ o escritório (pixel-agents) como fundo da área de trabalho
let fundo = { noAr: null, url: '', falhas: 0, ligando: 0 };
async function fundoEscritorio() {
  let d; try { d = await api('/api/app/escritorio'); } catch { return; }
  if (typeof d.no_ar !== 'boolean') return; // resposta com erro: não mexe no que está na tela
  if (d.no_ar) fundo.falhas = 0;
  else if (fundo.noAr && ++fundo.falhas < 3) return; // uma demora do pixel-agents não derruba o escritório
  if (d.no_ar === fundo.noAr && (d.url || '') === fundo.url) {
    const b = $('#ligar'); // a ligação falhou (sem Node, porta ocupada): deixa tentar de novo
    if (b && b.disabled && Date.now() - fundo.ligando > 90000) { b.disabled = false; b.textContent = 'Tentar ligar de novo'; }
    return;
  }
  fundo.noAr = d.no_ar; fundo.url = d.url || '';
  if (d.no_ar) { $('#fundo').innerHTML = `<iframe id="escritorio" src="${esc(d.url)}" title="Escritório de agentes (pixel-agents)" allow="clipboard-write"></iframe>`; return; }
  $('#fundo').innerHTML = `<div class="papel-parede"><img src="/web/logo-marfim.svg" alt=""><b>CIELLO</b><span>assistente comercial</span>
    <button class="bt ouro" id="ligar">Ligar o escritório</button><small>O escritório de agentes (pixel-agents) é o fundo desta área de trabalho.</small></div>`;
  $('#ligar').onclick = async (e) => {
    e.target.disabled = true; e.target.textContent = 'Ligando… (até 1 minuto na 1ª vez)'; fundo.ligando = Date.now();
    try { await api('/api/escritorio/ligar', {}); } catch { e.target.disabled = false; }
  };
}

// a ponte (web/ponte-escritorio.js, dentro do escritório) avisa quando um personagem é clicado
function agenteDoRotulo(rotulo) {
  const t = String(rotulo || '').split(':')[0].trim().toLowerCase();
  if (!t) return null;
  const a = equipeCache.find((x) => x.nome === t || x.nome.replace(/-/g, ' ') === t || nome(x.nome).toLowerCase() === t);
  return a ? a.nome : null;
}
const noEscritorio = {}; // agente -> o que estava fazendo no escritório quando foi clicado (vale 10 min)
const tarefaNoEscritorio = (a) => (noEscritorio[a] && Date.now() - noEscritorio[a].quando < 600000 ? noEscritorio[a].tarefa : '');
function abrirDoEscritorio(agente, tarefa) {
  noEscritorio[agente] = tarefa ? { tarefa, quando: Date.now() } : null;
  const j = janelas.get(`agente:${agente}`);
  if (j) desenhar(j, true);
  abrir(`agente:${agente}`);
}
window.addEventListener('message', (e) => {
  const f = $('#escritorio');
  if (e.origin !== location.origin || !f || e.source !== f.contentWindow || !e.data || e.data.ciello !== 'escritorio') return;
  if (e.data.evento === 'terminou') { // o subagente acabou: some o "pedido no escritório" da janela dele
    (e.data.rotulos || []).map(agenteDoRotulo).filter(Boolean).forEach((a) => { noEscritorio[a] = null; const j = janelas.get(`agente:${a}`); if (j) desenhar(j, true); });
    return;
  }
  if (e.data.evento !== 'clique') return;
  const proprio = agenteDoRotulo(e.data.nome);
  if (proprio) return void abrirDoEscritorio(proprio, '');
  // o coordenador e os subagentes dele dividem o mesmo id: abre quem está trabalhando com ele ("sdr: follow-ups" -> SDR)
  const porAgente = new Map();
  for (const r of e.data.ajudantes || []) {
    const a = agenteDoRotulo(r); if (!a) continue;
    porAgente.set(a, [...(porAgente.get(a) || []), r.split(':').slice(1).join(':').trim()]);
  }
  if (porAgente.size) return void [...porAgente].slice(-3).forEach(([a, t]) => abrirDoEscritorio(a, t.join(' · ')));
  abrir('equipe');
});

// ------------------------------------------------------------------ apps: bom dia
async function renderBriefing(j) {
  const d = await api('/api/app/briefing');
  const h = new Date().getHours(); const saud = h < 12 ? 'Bom dia' : h < 18 ? 'Boa tarde' : 'Boa noite';
  const data = new Date(`${d.data}T12:00:00`).toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' });
  const dono = (x) => (NOMES[x.dono] && x.dono !== 'Mateus') ? `<a data-abrir="agente:${esc(x.dono)}" style="cursor:pointer">${sprite(x.dono, 16)} ${esc(nome(x.dono))}</a>` : `${esc(nome(x.dono))}`;
  const top = d.itens.slice(0, 3); const resto = d.itens.slice(3);
  j.corpo.innerHTML = `<div class="saudacao"><img src="/web/logo-marfim.svg" alt=""><div><h1>${saud}, Mateus</h1><p>${esc(data)}</p></div></div>
  <div class="pagina"><h2>As 3 prioridades de hoje</h2><div class="lista">${top.map((x, i) => `<div class="prioridade"><span class="num">${i + 1}</span><div class="txt md">${md(x.texto).replace(/^<p>|<\/p>$/g, '')}<small>com ${dono(x)}</small></div></div>`).join('') || '<div class="vazio">Nada urgente. Bom dia para gravar conteúdo ou prospectar.</div>'}</div>
  <h2>Números</h2><div class="cartao md">${md(d.numeros.join('\n'))}</div>
  ${resto.length ? `<h2>Pendências</h2><div class="lista">${resto.map((x) => `<div class="linha-item"><div class="cresce md">${md(x.texto).replace(/^<p>|<\/p>$/g, '')}</div><small>${dono(x)}</small></div>`).join('')}</div>` : ''}
  <div class="acoes"><button class="bt pri" data-acao="briefing">${icone('play')} Atualizar briefing</button><button class="bt" data-acao="placar">Placar da semana</button><button class="bt" data-abrir="equipe">Equipe</button></div></div>`;
}

// ------------------------------------------------------------------ apps: financeiro
const brlCurto = (n) => `R$ ${Math.round(n ?? 0).toLocaleString('pt-BR')}`;
function barras(itens, fmt = brlCurto) {
  const max = Math.max(1, ...itens.map((i) => Math.abs(i.v)));
  return `<div class="barras">${itens.map((i) => `<div><b>${fmt(i.v)}</b><i style="height:${Math.max(3, 100 * Math.abs(i.v) / max) * 0.8}%;${i.cor ? `background:${i.cor}` : ''}"></i>${esc(i.r)}</div>`).join('')}</div>`;
}
async function renderFinanceiro(j) {
  const d = await api('/api/app/financeiro'); const s = d.situacao;
  const acoes = `<div class="acoes"><button class="bt pri" data-acao="fin_faturar">Faturas do mês</button><button class="bt" data-acao="fin_cobrar">Cobranças do dia</button><button class="bt" data-acao="posvenda">Pós-venda</button><button class="bt" data-acao="fin_resumo">Resumo completo</button></div>`;
  if (!s.tem_dados) {
    j.corpo.innerHTML = `<div class="pagina"><h1>Financeiro</h1><p class="sub">Assinaturas, cobrança, caixa e crescimento.</p><div class="vazio">Sem dados ainda. Cadastre o 1º cliente:<br><br><code>python central/financeiro.py cliente --empresa "Nome" --valor 149 --dia 10</code><br><br>e importe o extrato do banco em OFX: <code>financeiro.py importar extrato.ofx</code></div>${acoes}</div>`;
    return;
  }
  const atual = d.serie[d.serie.length - 1]; const mes = (m) => ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'][+m.slice(5) - 1];
  const kpi = (r, v, e = '', c = 'neutro') => `<div class="kpi"><small>${r}</small><strong>${v}</strong><em class="${c}">${e}</em></div>`;
  const atraso = s.atrasadas.reduce((t, f) => t + f.valor, 0);
  j.corpo.innerHTML = `<div class="pagina"><h1>Financeiro</h1><p class="sub">${num(s.clientes_ativos)} clientes ativos · despesa média ${brl(s.despesa_media)}/mês</p>
  <div class="kpis">${kpi('MRR', brl(s.mrr), `ARPA ${brl(atual.arpa)}`)}${kpi('Caixa hoje', brl(s.caixa), `30 dias: ${brl(s.previsao['30'])}`, s.previsao['30'] >= s.caixa ? 'bom' : 'ruim')}
  ${kpi('Atrasadas', s.atrasadas.length, s.atrasadas.length ? brl(atraso) : 'tudo em dia', s.atrasadas.length ? 'ruim' : 'bom')}${kpi('CAC', atual.cac != null ? brl(atual.cac) : '—', atual.payback != null ? `paga em ${atual.payback.toFixed(1).replace('.', ',')} meses` : 'sem cliente de anúncio no mês')}</div>
  <div class="grade2" style="margin-top:12px"><div class="cartao"><h2 style="margin-top:0">MRR · últimos 6 meses</h2>${barras(d.serie.map((m) => ({ r: mes(m.mes), v: m.mrr })))}</div>
  <div class="cartao"><h2 style="margin-top:0">Previsão de caixa</h2>${barras([{ r: 'hoje', v: s.caixa, cor: 'linear-gradient(180deg,#5E92E6,#2F5BA8)' }, ...['30', '60', '90'].map((k) => ({ r: `${k} dias`, v: s.previsao[k], cor: s.previsao[k] < s.caixa ? 'linear-gradient(180deg,#E9826C,#C8442F)' : undefined }))])}</div></div>
  ${s.alertas.length ? `<h2>Alertas</h2><div class="lista">${s.alertas.map((a) => `<div class="linha-item" style="border-left:4px solid var(--vermelho)">${esc(a)}</div>`).join('')}</div>` : ''}
  ${s.atrasadas.length ? `<h2>Faturas atrasadas</h2><div class="lista">${s.atrasadas.map((f) => `<div class="linha-item"><div class="cresce"><b>${esc(f.empresa)}</b><small>fatura #${esc(f.id)} · ${f.dias} dias de atraso</small></div><b>${brl(f.valor)}</b></div>`).join('')}</div>` : ''}
  <h2>Clientes</h2><table class="tab"><tr><th>Empresa</th><th>Mensalidade</th><th>Desde</th><th>NPS</th><th>Situação</th></tr>${d.clientes.map((c) => `<tr><td>${esc(c.empresa)}</td><td>${brl(+c.valor_mensal)}</td><td>${ddmm(c.inicio)}</td><td>${esc(c.nps || '—')}</td><td>${c.status === 'ativo' ? '<span class="chip pronto">ativo</span>' : '<span class="chip erro">cancelado</span>'}</td></tr>`).join('')}</table>
  ${Object.keys(atual.por_categoria).length ? `<h2>Despesas do mês por categoria</h2>${barras(Object.entries(atual.por_categoria).slice(0, 6).map(([r, v]) => ({ r, v, cor: 'linear-gradient(180deg,#8FA3C7,#3A5582)' })))}` : ''}
  ${acoes}</div>`;
}

// ------------------------------------------------------------------ apps: comercial
async function renderComercial(j) {
  const d = await api('/api/app/comercial');
  const acoes = `<div class="acoes"><button class="bt pri" data-acao="sdr_hoje">Follow-ups de hoje</button><button class="bt" data-acao="sdr_abordar">Abordar os 15 melhores</button><button class="bt" data-acao="sdr_crm">Exportar para o CRM</button><button class="bt" data-abrir="agente:sdr">SDR</button><button class="bt" data-abrir="agente:closer">Closer</button></div>`;
  if (!d.funil) {
    j.corpo.innerHTML = `<div class="pagina"><h1>Comercial</h1><p class="sub">Prospecção, follow-up e fechamento do CIELLO CRM.</p><div class="vazio">Sem leads ainda. No Claude Code: <code>/comercial</code>, ou <code>python central/sdr.py consultas</code> → <code>buscar</code> → <code>qualificar</code>.</div>${acoes}</div>`;
    return;
  }
  const topo = Math.max(1, d.funil.etapas[0].n);
  const lead = (l, extra = '') => `<div class="linha-item"><div class="cresce"><b>${esc(l.empresa)}</b><small>${esc([l.segmento, l.cidade, l.obs || l.dor_citada].filter(Boolean).join(' · '))}</small></div>${extra}</div>`;
  j.corpo.innerHTML = `<div class="pagina"><h1>Comercial</h1><p class="sub">${num(d.funil.total)} leads · ${num(d.funil.perdidos)} perdidos ou frios</p>
  <div class="grade2"><div class="cartao"><h2 style="margin-top:0">Funil</h2><div class="funil">${d.funil.etapas.map((e, i) => `<div><span>${esc(e.etapa)}</span><i style="width:${Math.max(2, 100 * e.n / topo)}%"></i><b>${e.n}</b><small>${i && d.funil.etapas[i - 1].n ? Math.round(100 * e.n / d.funil.etapas[i - 1].n) + '%' : ''}</small></div>`).join('')}</div></div>
  <div class="cartao"><h2 style="margin-top:0">Quentes · responder hoje</h2><div class="lista">${d.quentes.map((l) => lead(l, `<span class="chip esperando">${esc(l.etapa)}</span>`)).join('') || '<p class="sub">Ninguém esperando resposta.</p>'}</div></div></div>
  <h2>Follow-ups de hoje (${d.followups.length})</h2><div class="lista">${d.followups.map((l) => lead(l, `<small>último contato ${ddmm(l.ultimo_contato)}</small>`)).join('') || '<p class="sub">Nenhum follow-up para hoje.</p>'}</div>
  <h2>Melhores leads novos</h2><div class="lista">${d.novos.map((l) => lead(l, `<span class="chip pronto">${esc(l.pontos)} pts</span>`)).join('') || '<p class="sub">Fila vazia.</p>'}</div>${acoes}</div>`;
}

// ------------------------------------------------------------------ apps: conteúdo
async function renderConteudo(j) {
  const d = await api('/api/app/conteudo'); const i = d.instagram;
  const kpi = (r, v, e = '', c = 'neutro') => `<div class="kpi"><small>${r}</small><strong>${v}</strong><em class="${c}">${e}</em></div>`;
  const delta = i && i.seguidores_antes != null ? i.seguidores - i.seguidores_antes : null;
  j.corpo.innerHTML = `<div class="pagina"><h1>Conteúdo e Instagram</h1><p class="sub">@ciellotec${i ? ` · retrato de ${ddmm(i.data)}` : ''}</p>
  ${i ? `<div class="kpis">${kpi('Seguidores', num(i.seguidores), delta != null ? `${delta >= 0 ? '+' : ''}${delta} na semana` : '', delta >= 0 ? 'bom' : 'ruim')}${kpi('Alcance 30 dias', num(i.alcance))}
  ${kpi('Tempo médio no reel', `${String(i.tempo_medio).replace('.', ',')}s`, 'meta 6s', i.tempo_medio >= 6 ? 'bom' : 'ruim')}${kpi('Salvamentos', `${String(i.salvamentos_pct).replace('.', ',')}%`, 'meta 1%', i.salvamentos_pct >= 1 ? 'bom' : 'ruim')}</div>` : '<div class="vazio">Sem retrato do Instagram ainda: rode /segunda no Claude Code.</div>'}
  <h2>Posts · próximos e recentes</h2><div class="posts">${d.posts.map((p) => `<div class="post">${p.capa ? `<img src="${esc(p.capa)}" alt="" loading="lazy">` : '<div class="sem-capa"></div>'}<div><b>${ddmm(p.data)}</b>${esc(p.titulo)}<br>${p.final ? '<span class="chip pronto">vídeo pronto</span>' : '<span class="chip esperando">sem vídeo final</span>'}</div></div>`).join('')}</div>
  ${i && i.reels.length ? `<h2>Reels que mais alcançaram</h2><table class="tab"><tr><th>Data</th><th>Gancho</th><th>Alcance</th><th>Tempo</th></tr>${i.reels.map((r) => `<tr><td>${ddmm(r.data)}</td><td>${esc(r.gancho)}</td><td>${num(r.alcance)}</td><td>${String(r.tempo_medio_s ?? '').replace('.', ',')}s</td></tr>`).join('')}</table>` : ''}
  <div class="acoes"><button class="bt pri" data-acao="relatorio">Relatório semanal</button><button class="bt" data-acao="ganchos">Ranking de ganchos</button><button class="bt" data-abrir="agente:produtor-video">Produtor de vídeo</button><button class="bt" data-abrir="agente:postagem">Postagem</button></div></div>`;
}

// ------------------------------------------------------------------ apps: tendências e concorrentes
async function renderRelatorio(j, qual) {
  const d = await api(`/api/app/${qual}`);
  const acao = qual === 'tendencias' ? ['radar', 'Rodar o radar agora'] : ['vigia', 'Checar concorrentes agora'];
  const titulo = qual === 'tendencias' ? 'Tendências do nicho' : 'Concorrentes';
  const sub = qual === 'tendencias' ? 'Assuntos em alta nos 5 pilares, com nota de 0 a 100.' : `Vigiando ${esc((d.concorrentes || []).join(', '))}.`;
  j.corpo.innerHTML = `<div class="pagina"><h1>${titulo}</h1><p class="sub">${sub}${d.relatorio ? ` · <code>${esc(d.relatorio.arquivo)}</code>` : ''}</p>
  <div class="acoes" style="margin-top:0"><button class="bt pri" data-acao="${acao[0]}">${icone('play')} ${acao[1]}</button><button class="bt" data-abrir="agente:pesquisador-mercado">Pesquisador</button></div>
  ${d.relatorio ? `<div class="cartao md" style="margin-top:12px">${md(d.relatorio.texto)}</div>` : '<div class="vazio" style="margin-top:12px">Nenhum relatório ainda.</div>'}</div>`;
}

// ------------------------------------------------------------------ apps: anúncios
async function renderAnuncios(j) {
  const d = await api('/api/app/anuncios'); const r = d.resumo;
  const kpi = (t, v) => `<div class="kpi"><small>${t}</small><strong>${v}</strong></div>`;
  j.corpo.innerHTML = `<div class="pagina"><h1>Anúncios</h1><p class="sub">Testes no Meta Ads, lidos do Gerenciador de Anúncios ou do Metricool.</p>
  ${r ? `<div class="kpis">${kpi('Investido', brl(r.gasto))}${kpi('Conversas', num(r.conversas))}${kpi('Custo por conversa', r.custo_conversa != null ? brl(r.custo_conversa) : '—')}${kpi('Custo por cliente', r.custo_cliente != null ? brl(r.custo_cliente) : '—')}</div>
  <h2>Campanhas</h2><table class="tab"><tr><th>Campanha</th><th>Período</th><th>Gasto</th><th>Conversas</th><th>Demos</th><th>Clientes</th></tr>${d.campanhas.map((c) => `<tr><td><b>${esc(c.nome)}</b><br><small class="neutro">${esc(c.publico || '')}</small></td><td>${ddmm(c.inicio)}–${ddmm(c.fim)}</td><td>${brl(c.gasto)}</td><td>${num(c.conversas)}</td><td>${num(c.demos)}</td><td>${num(c.clientes)}</td></tr>`).join('')}</table>`
    : '<div class="vazio">Nenhuma campanha registrada em <code>anuncios/</code>. O gestor de anúncios grava cada teste lá.</div>'}
  <div class="acoes"><button class="bt pri" data-abrir="agente:gestor-anuncios">Gestor de anúncios</button></div></div>`;
}

// ------------------------------------------------------------------ apps: equipe, agente e atividade
async function renderEquipe(j) {
  if (!equipeCache.length) await puxarEquipe();
  j.corpo.innerHTML = `<div class="pagina"><h1>Equipe</h1><p class="sub">${equipeCache.length} agentes. Clique em um para ver o que ele faz e o que está fazendo agora.</p>
  <div class="grade2">${equipeCache.map((a) => { const s = estadoAgente(a.nome); return `<button class="cartao" data-abrir="agente:${esc(a.nome)}" style="display:flex;gap:12px;align-items:center;text-align:left;cursor:pointer">
    <span class="avatar" style="width:52px;height:52px;border-radius:12px;background:#E9E0C8;display:grid;place-items:center;flex:none">${sprite(a.nome, 30)}</span>
    <span style="min-width:0"><b>${esc(nome(a.nome))}</b> ${chipEstado(s.estado)}<small class="neutro" style="display:block;margin-top:3px;font-size:11.5px">${esc(s.estado !== 'parado' && s.tarefa ? s.tarefa : papel(a.descricao))}</small></span></button>`; }).join('')}</div></div>`;
}
async function renderAgente(j) {
  if (!equipeCache.length) await puxarEquipe();
  const a = equipeCache.find((x) => x.nome === j.def.agente) || { nome: j.def.agente, descricao: '', acoes: [] };
  const s = estadoAgente(a.nome);
  const eventos = estadoCache.eventos.filter((e) => e.agente === a.nome).slice(0, 10);
  const resto = a.descricao.split(': ').slice(1);
  j.corpo.innerHTML = `<div class="cab-agente"><div class="avatar">${sprite(a.nome, 44)}</div><div><h1>${esc(nome(a.nome))}</h1><p>${esc(papel(a.descricao))}</p><div style="margin-top:8px">${chipEstado(s.estado)} ${s.tarefa && s.estado !== 'parado' ? `<small class="neutro">${esc(s.tarefa)}</small>` : ''}${tarefaNoEscritorio(a.nome) ? `<small class="neutro" style="display:block;margin-top:4px">pedido no escritório: ${esc(tarefaNoEscritorio(a.nome))}</small>` : ''}</div></div></div>
  <div class="pagina"><h2 style="margin-top:0">O que faz</h2><p>${esc(resto.join(': ').replace(/ Use proactively.*$/, '') || a.descricao)}</p>
  ${a.acoes.length ? `<h2>Rodar agora</h2><div class="acoes" style="margin-top:0">${a.acoes.map((x, i) => `<button class="bt ${i ? '' : 'pri'}" data-acao="${esc(x.id)}">${icone('play')} ${esc(x.rotulo)}</button>`).join('')}</div>` : ''}
  ${COMANDOS[a.nome] ? `<h2>No Claude Code</h2><p class="comandos">${COMANDOS[a.nome].map((c) => `<code>${c}</code>`).join('')} ou "use o ${esc(a.nome)} para…"</p>` : ''}
  <h2>Últimas atividades</h2><div class="lista">${eventos.map((e) => `<div class="linha-item"><small style="width:46px">${esc(e.ts.slice(11, 16))}</small><div class="cresce">${esc(e.tarefa || '—')}</div>${chipEstado(e.estado)}</div>`).join('') || '<p class="sub">Ainda não trabalhou nesta sessão.</p>'}</div></div>`;
}
async function renderAtividade(j) {
  j.corpo.innerHTML = `<div class="pagina"><h1>Atividade</h1><p class="sub">O que cada agente e cada ferramenta fez, do mais novo para o mais antigo.</p><div class="lista">${estadoCache.eventos.map((e) =>
    `<div class="linha-item" data-abrir="agente:${esc(e.agente)}" style="cursor:pointer">${sprite(e.agente, 20)}<div class="cresce"><b>${esc(nome(e.agente))}</b><small>${esc(e.tarefa || '')}</small></div><small>${esc(e.ts.slice(11, 16))}</small>${chipEstado(e.estado)}</div>`).join('') || '<div class="vazio">Sem atividade ainda.</div>'}</div></div>`;
}

// ------------------------------------------------------------------ execução de uma ação (console ao vivo)
async function renderExecucao(j) {
  const id = j.chave.slice(5);
  const pintar = (ex) => {
    if (j.def.titulo !== ex.rotulo) { j.def = { ...j.def, titulo: ex.rotulo }; $('.titulo', j.el).textContent = ex.rotulo; barraTarefas(); }
    j.corpo.innerHTML = `<div class="exec"><div class="cab-exec">${sprite(ex.agente, 26)}<b>${esc(ex.rotulo)}<small class="neutro" style="display:block;font-weight:400">${esc(nome(ex.agente))} · começou às ${esc(ex.inicio)}</small></b>
      ${ex.terminou ? (ex.codigo === 0 ? '<span class="chip pronto">concluído</span>' : `<span class="chip erro">erro (código ${ex.codigo})</span>`) : '<span class="girando"></span>'}</div>
      <div class="saida"><pre class="console">${esc(ex.saida || 'Iniciando…')}</pre></div></div>`;
    const s = $('.saida', j.corpo); s.scrollTop = s.scrollHeight;
  };
  pintar(j.dados.id ? j.dados : { rotulo: 'Executando', agente: 'sistema', inicio: '', saida: '' });
  clearInterval(j.timerExec);
  j.timerExec = setInterval(async () => {
    let ex; try { ex = await api(`/api/execucao/${encodeURIComponent(id)}`); } catch { return; }
    if (ex.erro) { clearInterval(j.timerExec); return; }
    pintar(ex);
    if (ex.terminou) { clearInterval(j.timerExec); janelas.forEach((x) => { if (x !== j && !x.chave.startsWith('exec:')) desenhar(x, true); }); }
  }, 700);
}

// ------------------------------------------------------------------ início
async function iniciar() {
  barraTarefas(); relogio(); setInterval(relogio, 1000);
  fundoEscritorio(); setInterval(fundoEscritorio, 4000);
  await Promise.all([puxarEquipe(), puxarEstado()]);
  setInterval(puxarEstado, 1500); setInterval(puxarEquipe, 15000);
  const pedido = new URLSearchParams(location.hash.slice(1)).get('abrir');
  // um link só abre janelas (nunca roda ação) e no máximo 6
  const lista = (pedido ? pedido.split(',') : (SALVO.abertas.length ? SALVO.abertas : ['briefing'])).filter((k) => { const d = definicao(k); return d && !d.acao; }).slice(0, 6);
  lista.forEach((k) => abrir(k));
}
iniciar();
