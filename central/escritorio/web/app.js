/* Ciello OS: o escritório de agentes (pixel-agents) é o fundo da área de trabalho; barra de tarefas embaixo, apps no
   menu Iniciar e janelas que movem e redimensionam. Clicar num personagem do escritório abre a janela daquele agente.
   Os dados vêm do servidor local (central/escritorio/servidor.py); os botões só rodam as ações da lista dele. */
'use strict';
const TOKEN = window.CIELLO_TOKEN; delete window.CIELLO_TOKEN; // fica só aqui dentro, não em window

// ------------------------------------------------------------------ ícones (traço branco, 24x24)
const SVG = {
  atualizar: '<path d="M20 11a8 8 0 0 0-14.6-4.5L4 8M4 4v4h4M4 13a8 8 0 0 0 14.6 4.5L20 16M20 20v-4h-4"/>',
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
  engrenagem: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
  pino: '<path d="M12 17v5M9 3h6l-1 6 3 3v2H7v-2l3-3z"/>',
  play: '<path d="M7 5v14l11-7z"/>',
  redes: '<circle cx="6" cy="12" r="2.6"/><circle cx="18" cy="6" r="2.6"/><circle cx="18" cy="18" r="2.6"/><path d="M8.3 10.8l7.4-3.6M8.3 13.2l7.4 3.6"/>',
  conexoes: '<path d="M9 7V3M15 7V3M7 7h10v4a5 5 0 0 1-10 0z"/><path d="M12 16v5"/>',
  alvo: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2"/>',
  balao: '<path d="M4 5h16v11H9l-5 4z"/><path d="M8 9h8M8 12h5"/>',
  video: '<rect x="3" y="6" width="13" height="12" rx="2"/><path d="M16 10l5-3v10l-5-3z"/>',
  microfone: '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3M9 21h6"/>',
  min: '<path d="M2 6h8"/>', max: '<rect x="2" y="2" width="8" height="8"/>', rest: '<rect x="2" y="4" width="6" height="6"/><path d="M4 4V2h6v6H8"/>', fechar: '<path d="M2 2l8 8M10 2l-8 8"/>',
};
const icone = (n, vb = 24) => `<svg viewBox="0 0 ${vb} ${vb}">${SVG[n] || SVG.agente}</svg>`;

// ------------------------------------------------------------------ apps
const APPS = {
  redes: { titulo: 'Rede social', icone: 'redes', cor: 'linear-gradient(135deg,#F07A9B,#7B3FE4)', w: 960, h: 720, render: renderRedes },
  conexoes: { titulo: 'Conexões', icone: 'conexoes', cor: 'linear-gradient(135deg,#6FB0D8,#2F6A99)', w: 900, h: 700, render: renderConexoes },
  objetivos: { titulo: 'Gerente · objetivos e esteiras', icone: 'alvo', cor: 'linear-gradient(135deg,#F1C95A,#D99A0B)', w: 900, h: 700, render: renderObjetivos, cada: 3000 },
  atendimento: { titulo: 'Atendimento', icone: 'balao', cor: 'linear-gradient(135deg,#4CC6D1,#1E8C99)', w: 760, h: 680, render: renderAtendimento, estatico: true },
  video: { titulo: 'Estúdio de Vídeo', icone: 'video', cor: 'linear-gradient(135deg,#8E6BD8,#4B2F99)', w: 900, h: 720, render: renderVideo, estatico: true },
  voz: { titulo: 'Estúdio de Voz', icone: 'microfone', cor: 'linear-gradient(135deg,#E9826C,#B5442F)', w: 780, h: 700, render: renderVoz, estatico: true },
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
  atualizacoes: { titulo: 'Atualizações', icone: 'atualizar', cor: 'linear-gradient(135deg,#3A5582,#263A59)', w: 620, h: 520, render: renderAtualizacoes },
};
// menu Iniciar por objetivo: o que você quer fazer agora
const GRUPOS = [['Criar', ['redes', 'video', 'conteudo', 'voz', 'tendencias', 'concorrentes']], ['Vender', ['comercial', 'atendimento', 'anuncios']],
  ['Gerir', ['briefing', 'financeiro']], ['Equipe e sistema', ['conexoes', 'equipe', 'atividade', 'verificar', 'atualizacoes']]];

const NOMES = { gerente: 'Gerente', 'pesquisador-mercado': 'Pesquisador de Mercado', roteirista: 'Roteirista', 'produtor-video': 'Produtor de Vídeo',
  'produtor-imagem': 'Produtor de Imagem', postagem: 'Postagem', analista: 'Analista', 'gestor-anuncios': 'Gestor de Anúncios', sdr: 'SDR', closer: 'Closer',
  financeiro: 'Financeiro', 'caixa-entrada': 'Caixa de Entrada', 'sucesso-cliente': 'Sucesso do Cliente', sistema: 'Sistema', Mateus: 'Você' };
const CORES = { cyan: '#2FB7C4', blue: '#3B7BE0', green: '#2FA36B', orange: '#E07B39', pink: '#D9579A', purple: '#8E6BD8', red: '#D9533B', yellow: '#E0A81C' };
const COMANDOS = { gerente: ['/bom-dia', '/sexta'], financeiro: ['/bom-dia', '/sexta'], 'caixa-entrada': ['/bom-dia'], 'sucesso-cliente': ['/bom-dia'],
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
  if (chave.startsWith('term:')) {
    const rotulo = (SALVO.terminais || {})[chave.slice(5)];
    return { titulo: rotulo ? `Claude Code · ${rotulo}` : 'Claude Code', icone: 'terminal', cor: 'linear-gradient(135deg,#3A5582,#13213A)', w: 860, h: 540, render: renderTerminal, estatico: true };
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
  // tela de notebook (até 1440 px): na 1ª vez a janela abre maximizada, um app por vez; depois vale o tamanho que você deixou
  const notebook = !SALVO.geo[chave] && W < 1440 && !/^(term|exec):/.test(chave); // terminal e execução continuam em janela
  if (g.max || notebook) maximizar(j);
  ligarJanela(j);
  focar(j);
  desenhar(j);
  if (!def.estatico) j.timer = setInterval(() => { if (!j.min) (def.atualizar || desenhar)(j, true); }, def.cada || 20000);
  barraTarefas(); salvar();
  return j;
}

async function desenhar(j, silencioso) {
  const foco = document.activeElement;
  if (silencioso && foco && j.corpo.contains(foco) && foco.matches('input, select, textarea')) return;
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
  if (j.aoFechar) j.aoFechar();
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
  // campos com data-mudar: o select avisa ao escolher, a caixa de busca a cada letra
  const mudou = (e) => { const f = e.target.closest('[data-mudar]'); if (f && j.fns && j.fns[f.dataset.mudar] && (e.type === 'change') === (f.tagName === 'SELECT')) j.fns[f.dataset.mudar](f.dataset, f); };
  el.addEventListener('change', mudou); el.addEventListener('input', mudou);
  // caixa de objetivo: Enter manda para a equipe, Shift+Enter quebra a linha
  el.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey && e.target.matches('.objetivo-texto') && j.fns && j.fns.mandar) { e.preventDefault(); j.fns.mandar(); } });
  el.addEventListener('click', (e) => {
    const f = e.target.closest('[data-fn]');
    if (f && f.dataset.fn === 'aba') { e.preventDefault(); j.aba = f.dataset.aba; return desenhar(j, true); }
    if (f && j.fns && j.fns[f.dataset.fn]) { e.preventDefault(); return j.fns[f.dataset.fn](f.dataset, f); }
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
  $('#fixados').innerHTML = `<button class="fixado ${vazia ? 'ativa' : ''}" id="mostrar-escritorio" title="Mostrar o escritório (minimiza as janelas)">${tile({ cor: 'linear-gradient(135deg,#F1C95A,#D99A0B)', icone: 'escritorio' })}</button>`
    + `<button class="fixado" id="novo-terminal" title="Terminal do Claude Code: abre o Claude na pasta do assistente para ativar os agentes">${tile({ cor: 'linear-gradient(135deg,#3A5582,#13213A)', icone: 'terminal' })}</button>`
    + `<button class="fixado ${controles ? 'ligada' : ''}" id="engrenagem" title="${controles ? 'Esconder' : 'Mostrar'} os controles do escritório (+ Agente, Layout, Configurações, zoom)"><span class="tile">${icone('engrenagem')}</span></button>`;
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
$('#fixados').addEventListener('click', (e) => {
  if (e.target.closest('#engrenagem')) { controles = !controles; enviarControles(); barraTarefas(); return; }
  if (e.target.closest('#mostrar-escritorio')) mostrarEscritorio();
  if (e.target.closest('#novo-terminal')) abrirTerminal({});
});

// engrenagem: mostra ou esconde os botões nativos de personalização do pixel-agents (a ponte esconde por padrão)
let controles = false;
function enviarControles() { const f = $('#escritorio'); if (f && f.contentWindow) f.contentWindow.postMessage({ ciello: 'controles', ligado: controles }, location.origin); }

// Ctrl + scroll em qualquer lugar do app nunca dá zoom no navegador (no escritório, a ponte transforma em zoom do escritório)
window.addEventListener('wheel', (e) => { if (e.ctrlKey || e.metaKey) e.preventDefault(); }, { passive: false });

function desenharMenu(filtro = '') {
  const f = filtro.trim().toLowerCase();
  const casa = (k) => !f || APPS[k].titulo.toLowerCase().includes(f);
  const item = (k) => `<button class="item-app" data-chave="${k}">${tile(APPS[k])}<span>${esc(APPS[k].titulo)}</span></button>`;
  const grupos = GRUPOS.map(([g, ks]) => [g, ks.filter(casa)]).filter(([, ks]) => ks.length);
  const pedir = f.length >= 3 ? `<button class="pedir-equipe" data-pedir="1">${sprite('gerente', 24)}<span><b>Pedir à equipe</b><small>“${esc(filtro.trim())}”</small></span><kbd>Enter</kbd></button>` : '';
  $('#menu-apps').innerHTML = pedir
    + (!f ? `<button class="destaque-objetivo" data-chave="objetivos">${tile(APPS.objetivos)}<span><b>O que você quer fazer?</b><small>Escreva um objetivo ou rode uma esteira pronta: a equipe se organiza sozinha.</small></span></button>` : '')
    + grupos.map(([g, ks]) => `<h4>${g}</h4><div class="grupo-apps">${ks.map(item).join('')}</div>`).join('');
  $('#menu-equipe').innerHTML = equipeCache.filter((a) => nome(a.nome).toLowerCase().includes(f)).map((a) =>
    `<button class="item-agente" data-chave="agente:${esc(a.nome)}">${sprite(a.nome, 22)}<div><b>${esc(nome(a.nome))}</b><small>${esc(ROTULO_ESTADO[estadoAgente(a.nome).estado] || 'livre')}</small></div></button>`).join('');
}
function fecharMenus() { $('#menu').hidden = true; $('#central').hidden = true; $('#iniciar').classList.remove('on'); }
$('#iniciar').onclick = (e) => { e.stopPropagation(); const abrirMenu = $('#menu').hidden; fecharMenus(); if (abrirMenu) { desenharMenu(); $('#menu').hidden = false; $('#iniciar').classList.add('on'); $('#busca').value = ''; $('#busca').focus(); } };
$('#busca').oninput = (e) => desenharMenu(e.target.value);
// Enter na busca: abre o app se o texto é o nome dele; frase é objetivo e vai para a equipe
$('#busca').onkeydown = (e) => {
  if (e.key !== 'Enter') return;
  const t = e.target.value.trim(); if (!t) return;
  const app = Object.keys(APPS).find((k) => APPS[k].titulo.toLowerCase().includes(t.toLowerCase()) && !APPS[k].acao);
  if (app && t.split(/\s+/).length <= 2) abrir(app); else pedirEquipe(t);
};
$('#menu').addEventListener('click', (e) => { if (e.target.closest('[data-pedir]')) return pedirEquipe($('#busca').value.trim()); const b = e.target.closest('[data-chave]'); if (b) abrir(b.dataset.chave); });
$('#auto').checked = SALVO.auto; $('#auto').onchange = (e) => { SALVO.auto = e.target.checked; salvar(); };
$('#organizar').onclick = () => { fecharMenus(); organizar(); };
$('#centralizar').onclick = () => { fecharMenus(); const f = $('#escritorio'); if (f) f.contentWindow.postMessage({ ciello: 'centralizar' }, location.origin); };
$('#ver-escritorio').onclick = alternarEscritorio;
$('#minimizar-tudo').onclick = () => { fecharMenus(); mostrarEscritorio(); };
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

// ------------------------------------------------------------------ o escritório de agentes como fundo da área de trabalho
let fundo = { noAr: null, url: '' };
// modo foco: o escritório some (o iframe sai, sem gastar o PC) e fica só a logo da Ciello no centro
function papelParede(aviso = '') {
  $('#fundo').innerHTML = `<div class="papel-parede"><img src="/web/logo-marfim.svg" alt=""><b>CIELLO</b><span>assistente comercial</span>${aviso}</div>`;
}
function botaoEscritorio() { const b = $('#ver-escritorio'); if (b) b.textContent = SALVO.semEscritorio ? 'Mostrar escritório' : 'Esconder escritório'; }
function alternarEscritorio() {
  fecharMenus();
  SALVO.semEscritorio = !SALVO.semEscritorio; salvar(); botaoEscritorio();
  fundo = { noAr: null, url: '' };
  fundoEscritorio();
}
async function fundoEscritorio() {
  botaoEscritorio();
  if (SALVO.semEscritorio) {
    if (fundo.noAr !== 'foco') { fundo = { noAr: 'foco', url: '' }; papelParede(); }
    return;
  }
  let d; try { d = await api('/api/app/escritorio'); } catch { return; }
  if (typeof d.no_ar !== 'boolean') return; // resposta com erro: não mexe no que está na tela
  if (d.no_ar === fundo.noAr && (d.url || '') === fundo.url) return;
  fundo.noAr = d.no_ar; fundo.url = d.url || '';
  if (d.no_ar) {
    $('#fundo').innerHTML = `<iframe id="escritorio" src="${esc(d.url)}" title="Escritório de agentes" allow="clipboard-write"></iframe>`;
    $('#escritorio').addEventListener('load', enviarControles);
    return;
  }
  papelParede('<small>O escritório de agentes está desligado (o Ciello OS foi aberto com --sem-escritorio).</small>');
}

// a tela do escritório (escritorio/webview-ui/src/ciello) avisa quando um personagem é clicado
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
  if (e.data.evento === 'novoAgente') return void abrirTerminal({});
  if (e.data.evento !== 'clique') return;
  const proprio = agenteDoRotulo(e.data.nome);
  if (proprio === 'gerente') return void abrir('objetivos'); // o Gerente é com quem você fala: abre a caixa de objetivos
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

// ------------------------------------------------------------------ operação sem o Claude: formulários nas janelas
// Os formulários chamam as ferramentas do PC direto (servidor: /api/operar e /api/enviar → central/escritorio/operacao.py).
// Nada é enviado a ninguém daqui: as mensagens aparecem prontas com o link do WhatsApp e você envia.
const SEM_CLAUDE = '<p class="sem-claude">Funciona sem o Claude: tudo nesta janela roda direto no seu PC.</p>';
const linkar = (t) => esc(t).replace(/https?:\/\/[^\s<]+/g, (u) => `<a href="${u}" target="_blank" rel="noopener">${u.includes('wa.me/') ? 'Abrir no WhatsApp' : u}</a>`);
const hojeISO = () => { const d = new Date(); return new Date(d - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10); };
const wa = (link, rotulo = 'Abrir no WhatsApp') => (link ? `<a class="bt wa" href="${esc(link)}" target="_blank" rel="noopener">${rotulo}</a>` : '<small class="neutro">sem WhatsApp: ligar</small>');
const zap = (fone) => { const d = String(fone || '').replace(/\D/g, ''); return d ? `https://wa.me/${d.length <= 11 ? '55' + d : d}` : ''; };

function redesenharTudo() {
  if (document.activeElement && document.activeElement.matches('select')) document.activeElement.blur(); // a lista escolhida não segura a atualização
  janelas.forEach((x) => { if (!x.def.estatico) desenhar(x, true); });
}

async function operar(op, dados) {
  let r;
  try { r = await api('/api/operar', { op, dados }); } catch { return { ok: false, saida: 'Servidor desligado: abra o Ciello.cmd de novo.' }; }
  if (r.erro) r = { ok: false, saida: r.erro };
  if (r.ok) redesenharTudo();
  return r;
}
async function enviarArquivo(tipo, arquivo, opcoes = {}) {
  const q = new URLSearchParams({ tipo, nome: arquivo.name, ...opcoes });
  try {
    const r = await fetch(`/api/enviar?${q}`, { method: 'POST', headers: { 'X-Ciello-Token': TOKEN, 'Content-Type': 'application/octet-stream' }, body: arquivo });
    const d = await r.json(); if (d.ok) redesenharTudo(); return d.erro ? { ok: false, saida: d.erro } : d;
  } catch { return { ok: false, saida: 'Servidor desligado: abra o Ciello.cmd de novo.' }; }
}
// um clique que roda direto (sem formulário), com aviso do resultado
async function rapido(op, dados, titulo) {
  const r = await operar(op, dados);
  aviso({ titulo: r.ok ? titulo : 'Não deu certo', texto: r.saida, cor: r.ok ? '#1F8A4C' : '#C8442F' });
  return r;
}
async function copiar(texto) {
  try { await navigator.clipboard.writeText(texto); aviso({ titulo: 'Copiado', texto: 'Cole no WhatsApp.', cor: '#3A5582' }); } catch { /* sem permissão */ }
}

/* Diálogo dentro da janela. campos: [{ nome, rotulo, tipo: texto|numero|data|mes|escolha|area|sim|arquivo|marcar, opcoes, valor, dica, obrigatorio, meia }]
   enviar(dados) devolve { ok, saida }; o resultado aparece no próprio diálogo (com os links clicáveis). */
function dialogo(j, { titulo, texto = '', campos = [], botao = 'Salvar', enviar, extra = '' }) {
  $('.dialogo', j.el)?.remove();
  const el = document.createElement('div'); el.className = 'dialogo';
  const campo = (c) => {
    const id = `c-${c.nome}`; const v = c.valor ?? '';
    const req = c.obrigatorio ? ' required' : '';
    let input;
    if (c.tipo === 'escolha') input = `<select name="${c.nome}" id="${id}"${req}>${(c.opcoes || []).map((o) => { const [val, rot] = Array.isArray(o) ? o : [o, o]; return `<option value="${esc(val)}" ${String(val) === String(v) ? 'selected' : ''}>${esc(rot)}</option>`; }).join('')}</select>`;
    else if (c.tipo === 'area') input = `<textarea name="${c.nome}" id="${id}" rows="3"${req}>${esc(v)}</textarea>`;
    else if (c.tipo === 'sim') return `<label class="sim"><input type="checkbox" name="${c.nome}" ${v ? 'checked' : ''}> ${esc(c.rotulo)}</label>`;
    else if (c.tipo === 'marcar') return `<fieldset class="marcar"><legend>${esc(c.rotulo)}</legend>${(c.opcoes || []).map((o) => `<label><input type="checkbox" name="${c.nome}" value="${esc(o)}" ${(c.valor || []).includes(o) ? 'checked' : ''}> ${esc(o)}</label>`).join('')}</fieldset>`;
    else if (c.tipo === 'arquivo') input = `<input type="file" name="${c.nome}" id="${id}" accept="${esc(c.aceita || '')}"${req}>`;
    else input = `<input name="${c.nome}" id="${id}" type="${{ data: 'date', mes: 'month', datahora: 'datetime-local' }[c.tipo] || 'text'}" ${c.tipo === 'numero' ? 'inputmode="decimal"' : ''} value="${esc(v)}" placeholder="${esc(c.exemplo || '')}"${req}>`;
    return `<label class="campo ${c.meia ? 'meia' : ''}" for="${id}"><span>${esc(c.rotulo)}${c.obrigatorio ? ' *' : ''}</span>${input}${c.dica ? `<small>${esc(c.dica)}</small>` : ''}</label>`;
  };
  el.innerHTML = `<form class="caixa-dialogo" novalidate><header><b>${esc(titulo)}</b><button type="button" class="x" title="Fechar">${icone('fechar', 12)}</button></header>
    <div class="corpo-dialogo">${texto ? `<p class="sub">${texto}</p>` : ''}<div class="campos">${campos.map(campo).join('')}</div>${extra}<div class="resultado" hidden></div></div>
    <footer><button type="button" class="bt cancelar">Cancelar</button><button type="submit" class="bt pri">${esc(botao)}</button></footer></form>`;
  j.el.appendChild(el);
  const form = $('form', el); const res = $('.resultado', el);
  const campoForm = (nome) => form.elements.namedItem(nome); // namedItem: um campo chamado "item" não vira o método item()
  const sair = () => el.remove();
  $('.x', el).onclick = sair; $('.cancelar', el).onclick = sair;
  el.addEventListener('keydown', (e) => { if (e.key === 'Escape') { e.stopPropagation(); sair(); } });
  form.onsubmit = async (e) => {
    e.preventDefault();
    const dados = {};
    for (const c of campos) {
      if (c.tipo === 'marcar') dados[c.nome] = [...form.querySelectorAll(`[name="${c.nome}"]:checked`)].map((x) => x.value);
      else if (c.tipo === 'sim') dados[c.nome] = campoForm(c.nome).checked;
      else if (c.tipo === 'arquivo') dados[c.nome] = campoForm(c.nome).files[0] || null;
      else dados[c.nome] = campoForm(c.nome).value.trim();
      if (c.obrigatorio && !dados[c.nome]) { res.hidden = false; res.className = 'resultado erro'; res.textContent = `Preencha: ${c.rotulo}`; campoForm(c.nome)?.focus?.(); return; }
    }
    const b = $('[type=submit]', el); b.disabled = true; b.textContent = 'Salvando…';
    const r = await enviar(dados, form);
    b.disabled = false; b.textContent = botao;
    res.hidden = false; res.className = `resultado ${r.ok ? 'ok' : 'erro'}`;
    res.innerHTML = `<pre>${linkar(r.saida || (r.ok ? 'Pronto.' : 'Não deu certo.'))}</pre>`;
    if (r.ok) { $('.cancelar', el).textContent = 'Fechar'; b.style.display = 'none'; }
  };
  setTimeout(() => form.querySelector('input:not([type=checkbox]),select,textarea')?.focus(), 30);
  return el;
}
const formOp = (op, extra = {}) => (dados) => operar(op, { ...dados, ...extra });

// abas dentro de uma janela (a escolhida fica guardada na janela entre as atualizações)
function abas(j, lista) {
  j.aba = lista.some(([k]) => k === j.aba) ? j.aba : lista[0][0];
  return `<nav class="abas">${lista.map(([k, r, n]) => `<button class="${k === j.aba ? 'on' : ''}" data-fn="aba" data-aba="${k}">${esc(r)}${n ? ` <em>${n}</em>` : ''}</button>`).join('')}</nav>`;
}

// ------------------------------------------------------------------ apps: bom dia
// abre uma janela já na aba certa (atalhos do Bom dia)
function abrirAba(chave, aba) { const w = abrir(chave); if (w) { w.aba = aba; desenhar(w, true); } }
// abre a janela na aba e já abre o formulário (primeiros passos)
async function abrirAcao(chave, aba, fn) {
  const w = abrir(chave); if (!w) return;
  if (aba) w.aba = aba;
  await desenhar(w, true);
  if (fn && w.fns && w.fns[fn]) w.fns[fn]({});
}
const ATALHOS = [['redes', 'piloto', 'Rede social'], ['financeiro', 'cobranca', 'Cobrança e pós-venda'], ['comercial', 'hoje', 'Comercial de hoje'], ['conteudo', 'producao', 'Produção de conteúdo'], ['video', '', 'Estúdio de Vídeo'],
  ['financeiro', 'plano', 'Plano do ano'], ['voz', '', 'Estúdio de Voz'], ['objetivos', '', 'Esteiras da equipe']];
// cada pendência do Bom dia leva para a janela e a aba certas: pelo "Janela → Aba" do texto ou por uma pista
const DESTINOS = {
  Financeiro: ['financeiro', { 'Visão geral': 'geral', Clientes: 'clientes', 'Cobrança e pós-venda': 'cobranca', Lançamentos: 'lancamentos', 'Plano do ano': 'plano', 'Metas e decisões': 'rumo', 'Gerar faturas': 'geral' }],
  Comercial: ['comercial', { Hoje: 'hoje', Leads: 'leads', 'Buscar leads': 'buscar' }], Conteúdo: ['conteudo', { Produção: 'producao', Instagram: 'instagram', Análise: 'analise' }],
  Atendimento: ['atendimento', {}], 'Estúdio de Vídeo': ['video', {}], 'Estúdio de Voz': ['voz', {}], Conexões: ['conexoes', {}],
  'Rede social': ['redes', { Piloto: 'piloto', Comentários: 'comentarios', 'Calendário do mês': 'calendario', Resultados: 'resultados' }],
};
const PISTAS = [[/Retrato semanal/, ['conteudo', 'instagram']], [/Radar de tendências/, ['tendencias', '']], [/[Cc]oncorrente/, ['concorrentes', '']], [/Fila com/, ['comercial', 'buscar']],
  [/^Post de|post\(s\) com data passada/, ['conteudo', 'producao']], [/follow-up|lead\(s\) quente|[Dd]emo /, ['comercial', 'hoje']], [/Teste grátis/, ['financeiro', 'clientes']], [/espera sua aprovação/, ['equipe', '']]];
function destinoDoTexto(texto) {
  const m = String(texto).match(/(Financeiro|Comercial|Conteúdo|Atendimento|Estúdio de Vídeo|Estúdio de Voz|Rede social|Conexões)(?:\s*→\s*([A-Za-zÀ-ÿ\- ]+?))?(?=\s*(?:→|[:,.()]|$))/);
  if (m) { const [app, abasApp] = DESTINOS[m[1]]; return [app, (m[2] && abasApp[m[2].trim()]) || '']; }
  const p = PISTAS.find(([re]) => re.test(texto));
  return p ? p[1] : null;
}
const chaveItem = (texto) => String(texto).replace(/\d+([.,]\d+)?/g, '#').slice(0, 90);
async function renderBriefing(j) {
  const d = await api('/api/app/briefing');
  const hoje = hojeISO();
  SALVO.adiados = Object.fromEntries(Object.entries(SALVO.adiados || {}).filter(([, dia]) => dia === hoje));
  const adiados = d.itens.filter((x) => SALVO.adiados[chaveItem(x.texto)]);
  d.itens = d.itens.filter((x) => !SALVO.adiados[chaveItem(x.texto)]);
  j.fns = {
    mandar: () => { const t = $('.objetivo-texto', j.corpo); if (t.value.trim()) { pedirEquipe(t.value); t.value = ''; } else t.focus(); },
    atalho: ({ chave, aba }) => (aba ? abrirAba(chave, aba) : abrir(chave)),
    passo: ({ i }) => { const [c, a, f] = d.passos[+i].abrir; abrirAcao(c, a, f); },
    esconderPassos: () => { SALVO.semPassos = true; salvar(); desenhar(j, true); },
    ir: ({ i }) => { const [c, a] = destinoDoTexto(d.itens[+i].texto); if (a) abrirAba(c, a); else abrir(c); },
    hojeNao: ({ i }) => { SALVO.adiados[chaveItem(d.itens[+i].texto)] = hoje; salvar(); desenhar(j, true); },
    mostrarAdiados: () => { SALVO.adiados = {}; salvar(); desenhar(j, true); },
  };
  const feitos = d.passos.filter((x) => x.feito).length;
  const passos = feitos < d.passos.length && !SALVO.semPassos ? `<div class="cartao passos-inicio"><div class="cab-passos"><b>Primeiros passos · ${feitos} de ${d.passos.length}</b><i style="--p:${Math.round(100 * feitos / d.passos.length)}%"></i><button class="bt mini" data-fn="esconderPassos" title="Esconde este cartão">Esconder</button></div>
    <div class="lista">${d.passos.map((x, i) => `<div class="linha-item ${x.feito ? 'feito' : ''}"><span class="marca">${x.feito ? '✓' : i + 1}</span><div class="cresce"><b>${esc(x.titulo)}</b><small>${esc(x.porque)}</small></div>${x.feito ? '' : `<button class="bt mini pri" data-fn="passo" data-i="${i}">Fazer agora</button>`}</div>`).join('')}</div></div>` : '';
  const texto = $('.objetivo-texto', j.corpo)?.value || '';
  const h = new Date().getHours(); const saud = h < 12 ? 'Bom dia' : h < 18 ? 'Boa tarde' : 'Boa noite';
  const data = new Date(`${d.data}T12:00:00`).toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' });
  const dono = (x) => (NOMES[x.dono] && x.dono !== 'Mateus') ? `<a data-abrir="agente:${esc(x.dono)}" style="cursor:pointer">${sprite(x.dono, 16)} ${esc(nome(x.dono))}</a>` : `${esc(nome(x.dono))}`;
  const top = d.itens.slice(0, 3); const resto = d.itens.slice(3);
  const botoesItem = (x, i) => `${destinoDoTexto(x.texto) ? `<button class="bt mini" data-fn="ir" data-i="${i}" title="Abre a janela certa">Abrir</button>` : ''}<button class="bt mini fantasma" data-fn="hojeNao" data-i="${i}" title="Some daqui até amanhã">Hoje não</button>`;
  j.corpo.innerHTML = `<div class="saudacao"><img src="/web/logo-marfim.svg" alt=""><div><h1>${saud}, Mateus</h1><p>${esc(data)}</p></div></div>
  <div class="pagina"><div class="objetivo compacto"><textarea class="objetivo-texto" rows="1" placeholder="O que você quer que a equipe faça hoje? (Enter manda)">${esc(texto)}</textarea><button class="bt pri" data-fn="mandar">${icone('play')} Mandar</button></div>
  ${passos}<div class="atalhos">${ATALHOS.map(([c, a, r]) => `<button class="atalho" data-fn="atalho" data-chave="${c}" data-aba="${a}">${tile(APPS[c])}<span>${esc(r)}</span></button>`).join('')}</div>
  <h2>As 3 prioridades de hoje</h2><div class="lista">${top.map((x, i) => `<div class="prioridade"><span class="num">${i + 1}</span><div class="txt md">${md(x.texto).replace(/^<p>|<\/p>$/g, '')}<small>com ${dono(x)}</small></div><div class="acoes-item">${botoesItem(x, i)}</div></div>`).join('') || '<div class="vazio">Nada urgente. Bom dia para gravar conteúdo ou prospectar.</div>'}</div>
  <h2>Números</h2><div class="cartao md">${md(d.numeros.join('\n'))}</div>
  ${resto.length ? `<h2>Pendências</h2><div class="lista">${resto.map((x, k) => `<div class="linha-item"><div class="cresce md">${md(x.texto).replace(/^<p>|<\/p>$/g, '')}</div><small>${dono(x)}</small><div class="acoes-item">${botoesItem(x, k + 3)}</div></div>`).join('')}</div>` : ''}
  ${adiados.length ? `<p class="sub">${adiados.length} item(ns) deixado(s) para amanhã · <a href="#" data-fn="mostrarAdiados">mostrar de novo</a></p>` : ''}
  <div class="acoes"><button class="bt pri" data-acao="briefing">${icone('play')} Atualizar briefing</button><button class="bt" data-acao="placar">Placar da semana</button><button class="bt" data-abrir="equipe">Equipe</button></div></div>`;
}

// ------------------------------------------------------------------ apps: financeiro
const brlCurto = (n) => `R$ ${Math.round(n ?? 0).toLocaleString('pt-BR')}`;
function barras(itens, fmt = brlCurto) {
  const max = Math.max(1, ...itens.map((i) => Math.abs(i.v)));
  return `<div class="barras">${itens.map((i) => `<div><b>${fmt(i.v)}</b><i style="height:${Math.max(3, 100 * Math.abs(i.v) / max) * 0.8}%;${i.cor ? `background:${i.cor}` : ''}"></i>${esc(i.r)}</div>`).join('')}</div>`;
}
async function renderFinanceiro(j) {
  const [d, pl] = await Promise.all([api('/api/app/financeiro'), j.aba === 'plano' ? api('/api/app/plano') : j.aba === 'rumo' ? api('/api/app/rumo') : null]); const s = d.situacao;
  const nomeMes = (m) => ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'][+m.slice(5) - 1];
  const kpi = (r, v, e = '', c = 'neutro') => `<div class="kpi"><small>${r}</small><strong>${v}</strong><em class="${c}">${e}</em></div>`;
  const ativos = d.clientes.filter((c) => c.status === 'ativo');
  const porId = Object.fromEntries(d.clientes.map((c) => [c.id, c]));
  const clienteOpcoes = (lista) => lista.map((c) => [c.id, `#${c.id} · ${c.empresa}`]);
  const cats = ['', ...d.categorias];
  const P = d.produtos || {};

  // ---- formulários
  const camposCliente = (c = {}) => [
    { nome: 'empresa', rotulo: 'Empresa', valor: c.empresa, obrigatorio: !c.id, exemplo: 'Imobiliária Exemplo' },
    { nome: 'contato', rotulo: 'Contato (nome)', valor: c.contato, meia: true }, { nome: 'whatsapp', rotulo: 'WhatsApp', valor: c.whatsapp, exemplo: '49 99999-8888', meia: true },
    { nome: 'valor', rotulo: 'Mensalidade (R$)', tipo: 'numero', valor: c.valor_mensal ? String(+c.valor_mensal).replace('.', ',') : '', obrigatorio: !c.id, exemplo: '149,90', meia: true },
    { nome: 'dia', rotulo: 'Dia do vencimento', valor: c.dia_vencimento || (c.id ? '' : '10'), meia: true },
    { nome: 'plano', rotulo: 'Plano', valor: c.plano, meia: true },
    ...(c.id ? [{ nome: 'obs', rotulo: 'Observação', tipo: 'area', valor: c.obs }] : [{ nome: 'inicio', rotulo: 'Início', tipo: 'data', valor: hojeISO(), meia: true, dica: 'A 1ª fatura sai no 1º vencimento depois do início.' }]),
  ];
  j.fns = {
    novoCliente: () => dialogo(j, { titulo: 'Nova assinatura', texto: `CIELLO CRM${P.crm ? ` (${brl(P.crm.mensal)}/mês, ${P.crm.teste_dias} dias grátis)` : ''} ou hospedagem${P.hospedagem ? ` (${brl(P.hospedagem.mensal)}/mês)` : ''}. Em teste grátis, nada é faturado até você marcar <b>Virou cliente</b>.`,
      campos: [{ nome: 'produto', rotulo: 'Produto', tipo: 'escolha', opcoes: [['crm', `CIELLO CRM${P.crm ? ` · ${brl(P.crm.mensal)}/mês` : ''}`], ['hospedagem', `Hospedagem de site${P.hospedagem ? ` · ${brl(P.hospedagem.mensal)}/mês` : ''}`], ['', 'Outro (digite o valor)']], valor: 'crm', meia: true },
        { nome: 'teste', rotulo: 'Começa em teste grátis?', tipo: 'escolha', opcoes: [[String((P.crm || {}).teste_dias || 30), `Sim, ${(P.crm || {}).teste_dias || 30} dias`], ['0', 'Não, já paga']], meia: true },
        ...camposCliente().map((c) => (c.nome === 'valor' ? { ...c, obrigatorio: false, rotulo: 'Mensalidade (R$, se diferente)', exemplo: 'vazio = preço do produto' } : c)).filter((c) => c.nome !== 'plano')],
      botao: 'Cadastrar', enviar: (x) => operar('fin_cliente', { ...x, teste: x.produto === 'crm' ? x.teste : '0' }) }),
    venda: () => dialogo(j, { titulo: 'Venda de site', texto: `${P.site ? `${brl(P.site.avista)} à vista ou ${P.site.parcelas}x de ${brl(P.site.parcela)}` : 'Site'}${P.hospedagem ? `, mais a hospedagem de ${brl(P.hospedagem.mensal)}/mês` : ''}. As parcelas viram faturas e entram na previsão de caixa.`,
      campos: [{ nome: 'empresa', rotulo: 'Empresa', obrigatorio: true }, { nome: 'contato', rotulo: 'Contato (nome)', meia: true }, { nome: 'whatsapp', rotulo: 'WhatsApp', exemplo: '49 99999-8888', meia: true },
        { nome: 'forma', rotulo: 'Pagamento', tipo: 'escolha', opcoes: [['avista', P.site ? `À vista · ${brl(P.site.avista)}` : 'À vista'], ['parcelado', P.site ? `${P.site.parcelas}x de ${brl(P.site.parcela)}` : 'Parcelado']], meia: true },
        { nome: 'primeira', rotulo: '1º vencimento', tipo: 'data', valor: hojeISO(), meia: true },
        { nome: 'valor', rotulo: 'Valor combinado (R$, se diferente)', tipo: 'numero', exemplo: 'vazio = preço de lista', meia: true }, { nome: 'parcelas', rotulo: 'Parcelas (se diferente)', meia: true },
        { nome: 'com_hospedagem', rotulo: 'Hospedagem', tipo: 'escolha', opcoes: [['sim', `Sim${P.hospedagem ? `, ${brl(P.hospedagem.mensal)}/mês` : ''}`], ['nao', 'Não']], meia: true }, { nome: 'dia', rotulo: 'Dia de vencimento da hospedagem', valor: '10', meia: true }],
      botao: 'Registrar venda', enviar: ({ com_hospedagem: h, ...x }) => operar('fin_venda', { ...x, sem_hospedagem: h === 'nao' }) }),
    converter: ({ id }) => rapido('fin_converter', { id }, `${porId[id].empresa} virou cliente`),
    desistiu: ({ id }) => rapido('fin_cancelar', { id, motivo: 'não continuou depois do teste grátis' }, 'Teste encerrado'),
    editar: ({ id }) => dialogo(j, { titulo: `Editar ${porId[id].empresa}`, campos: camposCliente(porId[id]), enviar: formOp('fin_editar', { id }) }),
    cancelar: ({ id }) => dialogo(j, { titulo: `Cancelar ${porId[id].empresa}`, texto: 'O cliente sai do MRR e não recebe mais fatura. Dá para reativar depois.',
      campos: [{ nome: 'motivo', rotulo: 'Motivo', tipo: 'area', exemplo: 'preço, não usou, fechou a empresa…' }, { nome: 'data', rotulo: 'Data', tipo: 'data', valor: hojeISO() }], botao: 'Cancelar assinatura', enviar: formOp('fin_cancelar', { id }) }),
    reativar: ({ id }) => rapido('fin_editar', { id, reativar: true }, 'Cliente reativado'),
    conversa: ({ id }) => dialogo(j, { titulo: `Conversa com ${porId[id].empresa}`, texto: 'Ligação, visita ou WhatsApp: o que ficou combinado? A saúde da carteira conta os dias desde a última conversa.',
      campos: [{ nome: 'texto', rotulo: 'Resumo', tipo: 'area', obrigatorio: true, exemplo: 'Ex.: equipe usando, pediu ajuda com as etiquetas' }], enviar: (x) => operar('fin_conversa', { ...x, id }) }),
    nps: ({ id }) => dialogo(j, { titulo: 'Registrar NPS', texto: 'De 0 a 10, quanto o cliente recomendaria o CRM. 9–10 recebe o pedido de avaliação no Google; até 6 é risco de cancelamento.',
      campos: [{ nome: 'id', rotulo: 'Cliente', tipo: 'escolha', opcoes: clienteOpcoes(ativos), valor: id }, { nome: 'nota', rotulo: 'Nota', tipo: 'escolha', opcoes: [...Array(11).keys()].reverse().map(String), valor: '10' }],
      enviar: formOp('fin_nps') }),
    pagamento: ({ id }) => dialogo(j, { titulo: 'Registrar pagamento', texto: d.faturas_abertas.length ? 'Fatura recebida por Pix, boleto ou dinheiro.' : 'Nenhuma fatura em aberto. Gere as faturas do mês antes.',
      campos: [{ nome: 'id', rotulo: 'Fatura', tipo: 'escolha', opcoes: d.faturas_abertas.map((f) => [f.id, `#${f.id} · ${f.empresa} · ${f.competencia} · ${brl(f.valor)}`]), valor: id, obrigatorio: true }, { nome: 'data', rotulo: 'Pago em', tipo: 'data', valor: hojeISO() }],
      botao: 'Dar baixa', enviar: formOp('fin_pago') }),
    recebi: ({ id }) => rapido('fin_pago', { id }, 'Pagamento registrado'),
    lancar: () => dialogo(j, { titulo: 'Lançar receita ou despesa', texto: 'Para o que não vem no extrato do banco (Pix em outra conta, dinheiro). Um crédito que bate com uma fatura em aberto já dá baixa nela.',
      campos: [{ nome: 'tipo', rotulo: 'Tipo', tipo: 'escolha', opcoes: [['despesa', 'Despesa (saída)'], ['receita', 'Receita (entrada)']], meia: true }, { nome: 'valor', rotulo: 'Valor (R$)', tipo: 'numero', obrigatorio: true, exemplo: '59,90', meia: true },
        { nome: 'descricao', rotulo: 'Descrição', obrigatorio: true, exemplo: 'Canva Pro, Pix do cliente X…' }, { nome: 'categoria', rotulo: 'Categoria', tipo: 'escolha', opcoes: cats.map((c) => [c, c || 'automática (pelas regras)']), meia: true },
        { nome: 'data', rotulo: 'Data', tipo: 'data', valor: hojeISO(), meia: true }],
      botao: 'Lançar', enviar: ({ tipo, valor, ...r }) => operar('fin_lancar', { ...r, valor: (tipo === 'despesa' ? '-' : '') + valor.replace(/^-/, '') }) }),
    extrato: () => dialogo(j, { titulo: 'Importar extrato do banco', texto: 'Exporte o extrato no app ou site do banco em <b>OFX</b> (melhor) ou CSV. O Ciello classifica as despesas, dá baixa nas faturas pagas e pega o saldo. Pode importar o mesmo período de novo: nada duplica.',
      campos: [{ nome: 'arquivo', rotulo: 'Arquivo do extrato', tipo: 'arquivo', aceita: '.ofx,.csv', obrigatorio: true }], botao: 'Importar', enviar: ({ arquivo }) => enviarArquivo('extrato', arquivo) }),
    faturar: () => rapido('fin_faturar', { mes: d.mes }, `Faturas de ${nomeMes(d.mes)}`),
    caixa: () => dialogo(j, { titulo: 'Caixa e configurações', texto: 'O saldo do banco é o ponto de partida do caixa (o extrato OFX já atualiza sozinho).',
      campos: [{ nome: 'saldo', rotulo: 'Saldo do banco hoje (R$)', tipo: 'numero', valor: d.config.saldo_inicial ? String(d.config.saldo_inicial).replace('.', ',') : '', meia: true },
        { nome: 'data', rotulo: 'Data do saldo', tipo: 'data', valor: d.config.data_saldo || hojeISO(), meia: true },
        { nome: 'alerta', rotulo: 'Avisar se o caixa previsto ficar abaixo de (R$)', tipo: 'numero', valor: String(d.config.alerta_saldo).replace('.', ',') },
        { nome: 'link_avaliacao', rotulo: 'Link de avaliação no Google', valor: d.config.link_avaliacao, exemplo: 'https://g.page/r/…/review' },
        { nome: 'assinatura', rotulo: 'Assinatura das mensagens', valor: d.config.assinatura, meia: true }],
      enviar: (x) => operar('fin_config', { ...x, saldo: x.saldo && x.saldo !== String(d.config.saldo_inicial).replace('.', ',') ? x.saldo : '', data: x.saldo ? x.data : '' }) }),
    enviado: ({ tipo, id, etapa }) => rapido('fin_enviado', { tipo, id, etapa }, 'Registrado como enviado'),
    copiar: ({ i, lista }) => copiar(d[lista][+i].mensagem),
    categoria: ({ id }, el) => el.value && rapido('fin_categoria', { id, categoria: el.value }, 'Lançamento classificado'),
    reclassificar: () => rapido('fin_reclassificar', {}, 'Regras aplicadas'),
  };

  const barra = `<div class="acoes topo"><button class="bt pri" data-fn="novoCliente">+ Cliente</button><button class="bt" data-fn="venda">+ Venda de site</button><button class="bt" data-fn="pagamento">Registrar pagamento</button>
    <button class="bt" data-fn="lancar">Lançar receita/despesa</button><button class="bt" data-fn="extrato">Importar extrato</button>
    <button class="bt" data-fn="faturar" title="Cria as faturas de ${nomeMes(d.mes)} para os clientes ativos (não duplica)">Gerar faturas de ${nomeMes(d.mes)}</button><button class="bt" data-fn="caixa">Caixa</button></div>`;
  if (!s.tem_dados && !['plano', 'rumo'].includes(j.aba)) {  // plano e metas funcionam antes do 1º cliente
    j.corpo.innerHTML = `<div class="pagina"><h1>Financeiro</h1><p class="sub">Assinaturas, cobrança, caixa e crescimento.</p>${SEM_CLAUDE}${barra}
    <div class="passos"><h2>Para começar</h2><ol>
      <li><button class="bt pri" data-fn="novoCliente">Cadastrar uma assinatura</button> CRM (com ou sem teste grátis) ou hospedagem. Vendeu um site? <button class="bt" data-fn="venda">+ Venda de site</button></li>
      <li><button class="bt" data-fn="caixa">Informar o saldo do banco</button> é o ponto de partida do caixa.</li>
      <li><button class="bt" data-fn="extrato">Importar o extrato</button> (OFX ou CSV do banco): classifica as despesas e dá baixa nas faturas.</li></ol>
      <p class="sub">Quer planejar antes? <button class="bt mini" data-fn="aba" data-aba="plano">Plano do ano</button> <button class="bt mini" data-fn="aba" data-aba="rumo">Metas e decisões</button></p></div></div>`;
    return;
  }
  const atual = d.serie[d.serie.length - 1];
  const atraso = s.atrasadas.reduce((t, f) => t + f.valor, 0);
  const fila = d.cobrancas.length + d.posvenda.length;
  const msgCartao = (x, i, lista, titulo, botoes) => `<div class="cartao msg"><div class="cab"><b>${titulo}</b></div><pre class="texto-msg">${esc(x.mensagem)}</pre>
    <div class="acoes-linha">${wa(x.link)}<button class="bt" data-fn="copiar" data-lista="${lista}" data-i="${i}">Copiar</button>${botoes}</div></div>`;

  const ROT_PLANO = { crm: 'CRM', hospedagem: 'Hospedagem', site: 'Site' };
  // saúde da carteira (central/carteira.py): nota de 0 a 100, motivos e a mensagem para quem precisa de atenção
  const cart = d.carteira || { clientes: [], contagem: {}, promotores: [] };
  const saudePorId = Object.fromEntries(cart.clientes.map((s) => [s.id, s]));
  const SAUDE = { saudavel: ['trabalhando', 'saudável'], atencao: ['esperando', 'atenção'], risco: ['erro', 'risco'] };
  const chipSaude = (c) => { const s = saudePorId[c.id]; return s ? ` <span class="chip ${SAUDE[s.nivel][0]}" title="${esc(s.motivos.join(' · ') || 'tudo certo')}">${SAUDE[s.nivel][1]} ${s.nota}</span>` : ''; };
  d.carteira_acoes = cart.clientes.filter((s) => s.mensagem);
  const carteiraTopo = () => {
    if (!cart.clientes.length) return '';
    const k = cart.contagem;
    return `<div class="faixa-carteira"><b>Saúde da carteira</b><span class="chip trabalhando">${k.saudavel} saudáveis</span><span class="chip esperando">${k.atencao} em atenção</span><span class="chip erro">${k.risco} em risco</span>
      ${cart.mrr_em_risco ? `<small class="ruim">${brl(cart.mrr_em_risco)}/mês em risco</small>` : '<small class="neutro">nenhuma receita em risco</small>'}</div>
    ${cart.clientes.filter((s) => s.atraso > 3).map((s) => `<div class="linha-item" style="margin-bottom:6px"><div class="cresce"><b>${esc(s.empresa)}</b>${chipSaude(s)} <small class="neutro">${esc(s.motivos.join('; '))}</small></div><button class="bt mini pri" data-fn="aba" data-aba="cobranca">Cobrar</button></div>`).join('')}
    ${d.carteira_acoes.map((s, i) => msgCartao(s, i, 'carteira_acoes', `${esc(s.empresa)} ${chipSaude(s)} <small class="neutro">${esc(s.acao)} · ${esc(s.motivos.join('; ') || 'tudo certo')}</small>`,
      `<button class="bt pri" data-fn="conversa" data-id="${s.id}">Conversei</button>`)).join('')}`;
  };
  const situacaoCliente = (c) => {
    if (c.status === 'teste') { const t = s.testes.find((x) => x.id === c.id) || {}; return `<span class="chip ${t.dias <= 5 ? 'esperando' : 'trabalhando'}" title="teste grátis até ${ddmm(c.teste_ate)}">teste · ${t.dias < 0 ? 'acabou' : `${t.dias} dias`}</span>`; }
    if (c.status === 'ativo') return '<span class="chip pronto">ativo</span>';
    if (c.status === 'projeto') return '<span class="chip">site</span>';
    return `<span class="chip erro" title="${esc(c.motivo)}">cancelado</span>`;
  };
  let corpo = '';
  if (j.aba === 'plano' && pl) {
    corpo = planoCorpo(j, pl);
  } else if (j.aba === 'rumo' && pl) {
    corpo = rumoCorpo(j, pl);
  } else if (j.aba === 'clientes') {
    corpo = `${carteiraTopo()}<table class="tab"><tr><th>Empresa</th><th>Contato</th><th>Mensalidade</th><th>Vence</th><th>Desde</th><th>NPS</th><th>Situação</th><th></th></tr>${d.clientes.map((c) => `<tr>
      <td><b>${esc(c.empresa)}</b>${c.plano ? ` <small class="neutro">${esc(ROT_PLANO[c.plano] || c.plano)}</small>` : ''}${c.obs ? `<br><small class="neutro" title="${esc(c.obs)}">${esc(c.obs.split(' | ').pop())}</small>` : ''}</td><td>${esc(c.contato)}${c.whatsapp ? `<br><a href="${esc(zap(c.whatsapp))}" target="_blank" rel="noopener"><small>${esc(c.whatsapp)}</small></a>` : ''}</td>
      <td>${brl(+c.valor_mensal)}</td><td>dia ${esc(c.dia_vencimento)}</td><td>${ddmm(c.inicio)}</td><td>${esc(c.nps || '—')}</td>
      <td>${situacaoCliente(c)}${chipSaude(c)}</td>
      <td class="acoes-linha"><button class="bt mini" data-fn="editar" data-id="${c.id}">Editar</button>${c.status === 'teste' ? `<button class="bt mini pri" data-fn="converter" data-id="${c.id}">Virou cliente</button><button class="bt mini" data-fn="desistiu" data-id="${c.id}">Desistiu</button>`
        : c.status === 'ativo' ? `<button class="bt mini" data-fn="conversa" data-id="${c.id}" title="Registrar uma conversa (ligação, visita, WhatsApp)">Conversei</button><button class="bt mini" data-fn="nps" data-id="${c.id}">NPS</button><button class="bt mini" data-fn="cancelar" data-id="${c.id}">Cancelar</button>` : c.status === 'cancelado' ? `<button class="bt mini" data-fn="reativar" data-id="${c.id}">Reativar</button>` : ''}</td></tr>`).join('')}</table>`;
  } else if (j.aba === 'cobranca') {
    corpo = `<p class="sub">Mensagens prontas. Abra no WhatsApp, revise, envie e marque aqui. Nada é enviado sozinho.</p>
    <h2>Cobranças (${d.cobrancas.length})</h2>${d.cobrancas.map((x, i) => msgCartao(x, i, 'cobrancas', `${esc(x.empresa)} · ${brl(x.valor)} · ${x.dias} dias de atraso <span class="chip esperando">D+${x.etapa}</span>`,
      `<button class="bt" data-fn="enviado" data-tipo="cobranca" data-id="${x.fatura_id}" data-etapa="${x.etapa}">Enviei</button><button class="bt pri" data-fn="recebi" data-id="${x.fatura_id}">Recebi</button>`)).join('') || '<p class="sub">Nenhuma cobrança para hoje.</p>'}
    <h2>Pós-venda (${d.posvenda.length})</h2>${d.posvenda.map((x, i) => msgCartao(x, i, 'posvenda', `${esc(x.empresa)} <span class="chip pronto">${esc(x.rotulo)}</span>`,
      `<button class="bt" data-fn="enviado" data-tipo="posvenda" data-id="${x.cliente_id}" data-etapa="${x.etapa}">Enviei</button>${x.etapa === '30' ? `<button class="bt" data-fn="nps" data-id="${x.cliente_id}">Registrar NPS</button>` : ''}`)).join('') || '<p class="sub">Nenhum pós-venda para hoje.</p>'}`;
  } else if (j.aba === 'lancamentos') {
    corpo = `${gastosFixos(j, d.gastos)}${d.a_classificar.length ? `<h2>A classificar (${d.a_classificar.length})</h2><div class="lista">${d.a_classificar.map((l) => `<div class="linha-item"><div class="cresce"><b>${esc(l.descricao)}</b><small>${ddmm(l.data)} · ${esc(l.origem)}</small></div><b class="${+l.valor < 0 ? 'ruim' : 'bom'}">${brl(+l.valor)}</b>
      <select data-mudar="categoria" data-id="${l.id}"><option value="">categoria…</option>${d.categorias.map((c) => `<option>${esc(c)}</option>`).join('')}</select></div>`).join('')}</div>
      <div class="acoes"><button class="bt" data-fn="reclassificar" title="Aplica de novo as regras de financeiro/categorias.json">Reclassificar pelas regras</button></div>` : ''}
    <h2>Últimos lançamentos</h2><table class="tab"><tr><th>Data</th><th>Descrição</th><th>Categoria</th><th>Valor</th></tr>${d.lancamentos.map((l) => `<tr><td>${ddmm(l.data)}</td><td>${esc(l.descricao)}${l.fatura_id ? ` <small class="neutro">fatura #${esc(l.fatura_id)}</small>` : ''}</td><td>${esc(l.categoria)}</td><td class="${+l.valor < 0 ? 'ruim' : 'bom'}">${brl(+l.valor)}</td></tr>`).join('') || '<tr><td colspan="4">Nenhum lançamento: importe o extrato ou lance à mão.</td></tr>'}</table>`;
  } else {
    corpo = `<div class="kpis">${kpi('MRR', brl(s.mrr), `${num(s.clientes_ativos)} clientes · ARPA ${brl(atual.arpa)}`)}${kpi('Caixa hoje', brl(s.caixa), `30 dias: ${brl(s.previsao['30'])}`, s.previsao['30'] >= s.caixa ? 'bom' : 'ruim')}
    ${kpi('Atrasadas', s.atrasadas.length, s.atrasadas.length ? brl(atraso) : 'tudo em dia', s.atrasadas.length ? 'ruim' : 'bom')}${s.testes.length ? kpi('Em teste grátis', s.testes.length, `+${brl(s.mrr_em_teste)}/mês se todos fecharem`, s.testes.some((t) => t.dias <= 5) ? 'ruim' : 'neutro') : kpi('CAC', atual.cac != null ? brl(atual.cac) : '—', atual.payback != null ? `paga em ${atual.payback.toFixed(1).replace('.', ',')} meses` : 'sem cliente de anúncio no mês')}</div>
    ${s.sites_a_receber && s.sites_a_receber['90'] ? `<p class="sub" style="margin-top:8px">Sites a receber: ${brl(s.sites_a_receber['30'])} em 30 dias · ${brl(s.sites_a_receber['90'])} em 90 dias (já entram na previsão de caixa).</p>` : ''}
    ${!d.faturado_no_mes && ativos.length ? `<div class="faixa">As faturas de ${nomeMes(d.mes)} ainda não foram geradas. <button class="bt pri mini" data-fn="faturar">Gerar agora</button></div>` : ''}
    <div class="grade2" style="margin-top:12px"><div class="cartao"><h2 style="margin-top:0">MRR · últimos 6 meses</h2>${barras(d.serie.map((m) => ({ r: nomeMes(m.mes), v: m.mrr })))}</div>
    <div class="cartao"><h2 style="margin-top:0">Previsão de caixa</h2>${barras([{ r: 'hoje', v: s.caixa, cor: 'linear-gradient(180deg,#5E92E6,#2F5BA8)' }, ...['30', '60', '90'].map((k) => ({ r: `${k} dias`, v: s.previsao[k], cor: s.previsao[k] < s.caixa ? 'linear-gradient(180deg,#E9826C,#C8442F)' : undefined }))])}</div></div>
    ${s.alertas.length ? `<h2>Alertas</h2><div class="lista">${s.alertas.map((a) => `<div class="linha-item" style="border-left:4px solid var(--vermelho)">${esc(a)}</div>`).join('')}</div>` : ''}
    <h2>Faturas em aberto (${d.faturas_abertas.length})</h2><div class="lista">${d.faturas_abertas.map((f) => `<div class="linha-item"><div class="cresce"><b>${esc(f.empresa)}</b><small>fatura #${esc(f.id)} · ${esc(f.descricao || f.competencia)} · vence ${ddmm(f.vencimento)}${f.dias > 0 ? ` · <span class="ruim">${f.dias} dias de atraso</span>` : ''}</small></div><b>${brl(f.valor)}</b><button class="bt mini pri" data-fn="recebi" data-id="${f.id}">Recebi</button></div>`).join('') || '<p class="sub">Tudo pago.</p>'}</div>
    ${Object.keys(atual.por_categoria).length ? `<h2>Despesas do mês por categoria</h2>${barras(Object.entries(atual.por_categoria).slice(0, 6).map(([r, v]) => ({ r, v, cor: 'linear-gradient(180deg,#8FA3C7,#3A5582)' })))}` : ''}
    <div class="acoes"><button class="bt" data-acao="fin_resumo">Resumo completo</button><button class="bt" data-abrir="agente:financeiro">Agente Financeiro</button></div>`;
  }
  j.corpo.innerHTML = `<div class="pagina"><h1>Financeiro</h1><p class="sub">${num(s.clientes_ativos)} clientes ativos · despesa média ${brl(s.despesa_media)}/mês</p>${SEM_CLAUDE}${barra}
  ${abas(j, [['geral', 'Visão geral'], ['clientes', 'Clientes', d.clientes.length], ['cobranca', 'Cobrança e pós-venda', fila], ['lancamentos', 'Lançamentos', d.a_classificar.length + d.gastos.alertas.filter((a) => a.nivel !== 'dica').length || ''], ['plano', 'Plano do ano'], ['rumo', 'Metas e decisões']])}${corpo}</div>`;
}

// ------------------------------------------------------------------ financeiro: gastos fixos (central/gastos.py)
const TIPO_GASTO = { dobro: 'em dobro', subiu: 'subiu', parou: 'não veio', nova: 'nova', fora_do_plano: 'fora do plano' };
function gastosFixos(j, g) {
  if (!g || (!g.fixos.length && !g.alertas.length)) return '';
  Object.assign(j.fns, {
    paraPlano: ({ i, de }) => { const x = de === 'alerta' ? g.alertas[+i].item : g.fixos[+i];
      dialogo(j, { titulo: 'Pôr no Plano do ano', texto: 'O custo entra no plano como mensal. Ajuste o nome e o valor se precisar.',
        campos: [{ nome: 'item', rotulo: 'Custo', valor: x.rotulo || x.nome, obrigatorio: true }, { nome: 'valor', rotulo: 'Valor (R$)', tipo: 'numero', valor: String(x.valor).replace('.', ','), obrigatorio: true, meia: true },
          { nome: 'categoria', rotulo: 'Categoria', tipo: 'escolha', opcoes: ['ferramentas', 'servidor', 'infraestrutura', 'hospedagem', 'anuncios', 'contabilidade', 'terceiros', 'impostos', 'outros'], valor: g.para_o_plano[x.categoria] || 'ferramentas', meia: true }],
        enviar: (v) => operar('plano_item', { ...v, lista: 'custos', frequencia: 'mensal' }) }); },
  });
  const alertas = g.alertas.filter((a) => a.tipo !== 'fora_do_plano');
  const fora = g.alertas.filter((a) => a.tipo === 'fora_do_plano').length;
  return `<h2>Gastos fixos · ${brl(g.total_mensal)}/mês</h2><p class="sub" style="margin-top:0">O que o extrato mostra todo mês.${g.tem_plano ? ` No Plano do ano estão ${brl(g.plano_mensal)}/mês${fora ? `; ${fora} gasto(s) fixo(s) ainda fora dele` : ''}.` : ' Monte o Plano do ano para comparar.'}</p>
  ${alertas.length ? `<div class="lista">${alertas.map((a) => `<div class="linha-item achado ${a.nivel}"><span class="chip ${NIVEL[a.nivel][0]}">${TIPO_GASTO[a.tipo]}</span><div class="cresce"><small style="white-space:normal;font-size:12.5px;color:var(--tinta)">${esc(a.texto)}</small></div>${a.tipo === 'nova' && g.tem_plano ? `<button class="bt mini" data-fn="paraPlano" data-de="alerta" data-i="${g.alertas.indexOf(a)}">Pôr no plano</button>` : ''}</div>`).join('')}</div>` : ''}
  ${g.fixos.length ? `<table class="tab" style="margin-top:8px"><tr><th>Gasto</th><th>Valor</th><th>Mês anterior</th><th>Dia</th><th>Plano do ano</th></tr>${g.fixos.map((f, i) => `<tr><td><b>${esc(f.rotulo)}</b><br><small class="neutro">${esc(f.categoria)} · ${f.meses} meses no extrato</small></td>
    <td>${brl(f.valor)}</td><td class="${f.valor > f.anterior * 1.05 ? 'ruim' : 'neutro'}">${brl(f.anterior)}</td><td>${f.dia}</td>
    <td>${f.no_plano ? '<span class="chip pronto">no plano</span>' : g.tem_plano ? `<button class="bt mini" data-fn="paraPlano" data-i="${i}">Pôr no plano</button>` : '—'}</td></tr>`).join('')}</table>` : ''}`;
}

// ------------------------------------------------------------------ financeiro: plano do ano (central/plano.py)
const NIVEL = { alto: ['erro', 'importante'], medio: ['esperando', 'atenção'], dica: ['pronto', 'dica'] };
const PRODUTO_PLANO = [['crm', 'CIELLO CRM'], ['site', 'Site'], ['hospedagem', 'Hospedagem'], ['instagram', 'Instagram / conteúdo'], ['sistema', 'Sistema sob medida'], ['outro', 'Outro']];
function planoCorpo(j, pl) {
  const p = pl.plano; const proj = pl.projecao; const eq = pl.equilibrio;
  const soma = (k) => proj.reduce((t, m) => t + m[k], 0);
  const meses = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
  const pagam = proj.filter((m) => m.sobra_para_voce >= 0).length;
  const pct = (v) => String(Math.round((+v || 0) * 1000) / 10).replace('.', ',');
  const camposNegocio = (n = {}) => [{ nome: 'cliente', rotulo: 'Cliente', valor: n.cliente, obrigatorio: true }, { nome: 'produto', rotulo: 'Produto', tipo: 'escolha', opcoes: PRODUTO_PLANO, valor: n.produto || 'crm', meia: true },
    { nome: 'tipo', rotulo: 'Cobrança', tipo: 'escolha', opcoes: [['mensal', 'Mensal (recorrente)'], ['parcelas', 'Parcelas'], ['unico', 'Pagamento único']], valor: n.tipo || 'mensal', meia: true },
    { nome: 'valor', rotulo: 'Valor (R$, mês ou parcela)', tipo: 'numero', valor: n.valor != null ? String(n.valor).replace('.', ',') : '', obrigatorio: true, meia: true }, { nome: 'parcelas', rotulo: 'Nº de parcelas', valor: n.parcelas || '', meia: true },
    { nome: 'inicio', rotulo: 'Começa em', tipo: 'mes', valor: n.inicio || `${p.ano}-01`, meia: true }, { nome: 'fim', rotulo: 'Termina em (se termina)', tipo: 'mes', valor: n.fim || '', meia: true },
    { nome: 'status', rotulo: 'Situação', tipo: 'escolha', opcoes: [['fechado', 'Fechado'], ['negociando', 'Negociando (50%)'], ['talvez', 'Talvez (25%)']], valor: n.status || 'fechado', meia: true },
    { nome: 'chance', rotulo: 'Chance de fechar (%, se diferente)', valor: n.chance != null ? Math.round(n.chance * 100) : '', meia: true }];
  const camposCusto = (c = {}) => [{ nome: 'item', rotulo: 'Custo', valor: c.item, obrigatorio: true, exemplo: 'Servidor, Claude, contador…' }, { nome: 'valor', rotulo: 'Valor (R$)', tipo: 'numero', valor: c.valor != null ? String(c.valor).replace('.', ',') : '', obrigatorio: true, meia: true },
    { nome: 'frequencia', rotulo: 'Frequência', tipo: 'escolha', opcoes: [['mensal', 'Todo mês'], ['anual', 'Uma vez por ano'], ['unico', 'Só uma vez']], valor: c.frequencia || 'mensal', meia: true },
    { nome: 'mes', rotulo: 'Mês (anual ou único)', tipo: 'mes', valor: c.mes || '', meia: true }, { nome: 'categoria', rotulo: 'Categoria', tipo: 'escolha', opcoes: pl.categorias, valor: c.categoria || 'ferramentas', meia: true }];
  Object.assign(j.fns, {
    planoConfig: () => dialogo(j, { titulo: 'Regras do plano', texto: 'Quanto mais perto da realidade, mais útil a auditoria. Imposto e taxas são aproximações para planejar: confirme com o contador.',
      campos: [{ nome: 'ano', rotulo: 'Ano', valor: p.ano, meia: true }, { nome: 'regime', rotulo: 'Regime de imposto', tipo: 'escolha', opcoes: [['', 'Ainda não sei'], ...Object.entries(pl.regimes).map(([k, r]) => [k, r.nome])], valor: p.regime, meia: true },
        { nome: 'pro_labore', rotulo: 'Quanto você precisa tirar por mês (R$)', tipo: 'numero', valor: p.pro_labore ? String(p.pro_labore).replace('.', ',') : '' },
        { nome: 'churn_mensal', rotulo: 'Cancelamentos por mês (%)', valor: pct(p.churn_mensal), meia: true, dica: '3% é um bom começo para SaaS pequeno' }, { nome: 'taxa_recebimento', rotulo: 'Taxas de recebimento (%)', valor: pct(p.taxa_recebimento), meia: true, dica: '0 se recebe por Pix' }],
      extra: `<div class="lista">${Object.values(pl.regimes).map((r) => `<div class="linha-item"><div class="cresce"><b>${esc(r.nome)}</b><small style="white-space:normal">${esc(r.nota)}</small></div></div>`).join('')}</div>`,
      enviar: (x) => operar('plano_config', x) }),
    negocio: ({ i }) => dialogo(j, { titulo: i != null ? 'Editar negócio' : 'Novo negócio', texto: 'Cliente atual ou negociação. "Talvez" conta 25% do valor na receita provável.', campos: camposNegocio(i != null ? p.negocios[+i] : {}), enviar: (x) => operar('plano_item', { ...x, lista: 'negocios', i }) }),
    custo: ({ i }) => dialogo(j, { titulo: i != null ? 'Editar custo' : 'Novo custo', campos: camposCusto(i != null ? p.custos[+i] : {}), enviar: (x) => operar('plano_item', { ...x, lista: 'custos', i }) }),
    remover: ({ lista, i }) => { const it = p[lista][+i]; if (confirm(`Tirar "${it.cliente || it.item}" do plano?`)) rapido('plano_remover', { lista, i }, 'Removido do plano'); },
    simular: () => {
      const reg = pl.regimes[p.regime] || { aliquota: 0, fixo: 0 }; const taxa = +p.taxa_recebimento || 0;
      const alvo = eq.custos_fixos_mes + reg.fixo + (+p.pro_labore || 0);
      const n = (v) => +String(v || '0').replace(/\./g, '').replace(',', '.') || 0;
      const conta = (preco, anual, impl, novos) => { const medio = preco * (1 - (anual / 100) * (2 / 12)); const liq = medio * (1 - reg.aliquota - taxa);
        return { medio, liq, clientes: liq > 0 ? Math.ceil(alvo / liq) : null, impl_ano: impl * novos, adianta: preco * 10 }; };
      const base = conta(eq.preco_crm, 0, 0, 0);
      const el = dialogo(j, { titulo: 'Simular preço do CRM', texto: `Mude os números e veja na hora quantos clientes pagam ${p.pro_labore ? `os custos e os seus ${brl(p.pro_labore)}/mês` : 'os custos (informe o pró-labore em Regras do plano para a conta completa)'}. Nada muda no plano nem no preço.`,
        campos: [{ nome: 'preco', rotulo: 'Mensalidade (R$)', tipo: 'numero', valor: String(eq.preco_crm).replace('.', ','), meia: true }, { nome: 'anual', rotulo: '% dos clientes no plano anual (12 por 10)', tipo: 'numero', valor: '0', meia: true },
          { nome: 'impl', rotulo: 'Taxa de implantação (R$, uma vez)', tipo: 'numero', valor: '0', meia: true }, { nome: 'novos', rotulo: 'Clientes novos no ano', tipo: 'numero', valor: '12', meia: true }],
        extra: '<div class="sim-preco"></div>', botao: 'Discutir este cenário com o Financeiro',
        enviar: (x) => { const r = conta(n(x.preco), n(x.anual), n(x.impl), n(x.novos));
          pedirEquipe(`Use o agente financeiro. Quero discutir um cenário de preço do CIELLO CRM: mensalidade ${brl(n(x.preco))}, ${n(x.anual)}% dos clientes no plano anual (12 por 10), taxa de implantação de ${brl(n(x.impl))} e ${n(x.novos)} clientes novos no ano. Pela conta do OS, são ${r.clientes} clientes para pagar os custos${p.pro_labore ? ' e o pró-labore' : ''} (hoje, a ${brl(eq.preco_crm)}, são ${base.clientes}). Leia financeiro/plano.json, comercial/produtos.json, comercial/concorrentes.json e financeiro/regras.md. Me diga o que ganho e o que arrisco (conversão no teste grátis, cancelamento, posição frente aos concorrentes), e como testar sem queimar os clientes atuais. Não mude preço nem plano: a decisão é minha, em Financeiro → Metas e decisões.`, 'Financeiro · preço');
          return Promise.resolve({ ok: true, saida: 'O Financeiro vai discutir o cenário no terminal.' }); } });
      const pinta = () => { const f = $('form', el); const v = (k) => n(f.elements.namedItem(k).value); const r = conta(v('preco'), v('anual'), v('impl'), v('novos'));
        const dif = r.clientes != null && base.clientes != null ? r.clientes - base.clientes : 0;
        $('.sim-preco', el).innerHTML = `<div class="kpis">${[['Clientes para pagar a conta', r.clientes ?? '—', dif ? `${dif > 0 ? '+' : ''}${dif} contra hoje (${base.clientes})` : `igual a hoje`, dif > 0 ? 'ruim' : dif < 0 ? 'bom' : 'neutro'],
          ['Cada cliente deixa', brl(r.liq), `por mês, ${p.regime ? 'depois de imposto e taxas' : 'sem imposto (escolha o regime em Regras do plano)'}${v('anual') ? ` (média com anual: ${brl(r.medio)})` : ''}`],
          ['Implantação no ano', brl(r.impl_ano), v('impl') ? `${brl(v('impl'))} × ${v('novos')} clientes novos` : 'sem taxa'],
          ['Plano anual', v('anual') ? brl(r.adianta) : '—', v('anual') ? 'entra adiantado por cliente anual' : 'ninguém no anual']].map(([a, b, c, k]) => `<div class="kpi"><small>${a}</small><strong>${b}</strong><em class="${k || 'neutro'}">${c}</em></div>`).join('')}</div>`; };
      $('form', el).addEventListener('input', pinta); pinta();
    },
    trazerClientes: () => rapido('plano_importar', {}, 'Plano atualizado'),
    discutir: () => pedirEquipe(`Discuta comigo o plano ${p.ano} da Ciello como o agente financeiro. Rode \`python central/plano.py\`, leia o resultado (financeiro/relatorios/plano-${p.ano}.md e financeiro/plano.json) e comece pelos pontos marcados como importantes. Para cada um: o que significa na prática, 2 caminhos possíveis com os números, e a sua recomendação. Depois proponha 3 regras simples para a empresa seguir (ex.: quando cobrar implantação, quanto separar por mês, quando contratar) e um plano de implantação em etapas para os próximos 90 dias. Use /founder-cfo e /founder-pricing se ajudar. Não mude o plano nem os preços sem a minha aprovação.`, 'Financeiro · plano'),
    planilha: () => pedirEquipe(`Use o agente financeiro: leia no Google Drive a aba "NEGÓCIOS CIELLO" da planilha "CONTROLE PESSOAL" (só os números da empresa; nada pessoal, CPF ou conta). Monte financeiro/plano.json no formato do central/plano.py (negocios: cliente, produto, tipo mensal|parcelas|unico, valor, parcelas, inicio AAAA-MM, fim, status fechado|negociando|talvez; custos: item, valor, frequencia mensal|anual|unico, mes, categoria). Me mostre a lista antes de gravar, junte com o que já está no plano sem duplicar, e aponte o que na planilha parece errado ou faltando.`, 'Financeiro · planilha'),
  });
  if (!p.negocios.length && !p.custos.length) {
    return `<div class="passos"><h2>Monte o plano ${esc(p.ano)} em 3 passos</h2><ol>
      <li><button class="bt pri" data-fn="trazerClientes">Trazer os clientes do Financeiro</button> as assinaturas de hoje entram como negócios fechados. Depois, <button class="bt" data-fn="negocio">+ Negócio</button> para cada negociação (fechado, negociando ou talvez).</li>
      <li><button class="bt" data-fn="custo">+ Custo</button> ferramentas, servidor, domínios, contador, anúncios: mensais, anuais ou únicos.</li>
      <li><button class="bt" data-fn="planoConfig">Regras do plano</button> regime de imposto e quanto você precisa tirar por mês.</li></ol>
      <p class="sub">Já tem tudo numa planilha do Google? <button class="bt mini" data-fn="planilha">Puxar da planilha</button> (usa o Claude para ler e te mostra antes de gravar).</p></div>`;
  }
  return `<div class="faixa-plano"><div><b>Plano ${esc(p.ano)}</b> · ${esc((pl.regimes[p.regime] || {}).nome || 'regime de imposto não informado')} ${p.pro_labore ? ` · você precisa de ${brl(p.pro_labore)}/mês` : ''}</div>
    <div class="acoes-linha"><button class="bt mini" data-fn="planoConfig">Regras do plano</button><button class="bt mini" data-fn="simular">Simular preço</button><button class="bt mini" data-fn="planilha" title="Usa o Claude para ler a sua planilha do Google Drive">Puxar da planilha</button><button class="bt mini pri" data-fn="discutir">Discutir com o Financeiro</button></div></div>
  <div class="kpis">${[['Receita provável no ano', brl(soma('receita_provavel')), `se tudo fechar: ${brl(soma('receita_se_tudo_fechar'))}`],
    ['Resultado do ano', brl(soma('resultado')), `impostos ${brl(soma('imposto'))} · custos ${brl(soma('custos'))}`, soma('resultado') >= 0 ? 'bom' : 'ruim'],
    ['Te paga em', p.pro_labore ? `${pagam} de 12 meses` : '—', p.pro_labore ? `meta ${brl(p.pro_labore)}/mês` : 'informe em Regras do plano', p.pro_labore ? (pagam === 12 ? 'bom' : 'ruim') : 'neutro'],
    ['Clientes de CRM para te pagar', p.pro_labore ? (eq.clientes_para_te_pagar ?? '—') : '—', `${brl(eq.liquido_por_cliente)} líquido cada`]].map(([r, v, e, c]) => `<div class="kpi"><small>${r}</small><strong>${v}</strong><em class="${c || 'neutro'}">${e}</em></div>`).join('')}</div>
  <h2>O que olhar (${pl.auditoria.length})</h2><div class="lista">${pl.auditoria.map((a) => `<div class="linha-item achado ${a.nivel}"><span class="chip ${NIVEL[a.nivel][0]}">${NIVEL[a.nivel][1]}</span><div class="cresce"><b>${esc(a.titulo)}</b><small style="white-space:normal">${esc(a.detalhe)}</small></div></div>`).join('') || '<p class="sub">Nada a apontar.</p>'}</div>
  <div class="cartao" style="margin-top:12px"><h2 style="margin-top:0">Resultado mês a mês ${p.pro_labore ? `· a linha é o seu pró-labore (${brl(p.pro_labore)})` : ''}</h2>
    <div class="barras-plano">${proj.map((m) => { const max = Math.max(1, ...proj.map((x) => Math.abs(x.resultado)), +p.pro_labore || 0); return `<div title="${esc(m.mes)}: receita ${brl(m.receita_provavel)} · resultado ${brl(m.resultado)}"><b>${brlCurto(m.resultado)}</b><i style="height:${Math.max(2, 100 * Math.abs(m.resultado) / max) * 0.8}%" class="${m.sobra_para_voce >= 0 ? 'ok' : 'falta'}"></i>${p.pro_labore ? `<u style="bottom:${(100 * p.pro_labore / max) * 0.8 + 18}px"></u>` : ''}${meses[+m.mes.slice(5) - 1]}</div>`; }).join('')}</div></div>
  <h2>Negócios (${p.negocios.length})</h2><div class="acoes" style="margin-top:0"><button class="bt pri mini" data-fn="negocio">+ Negócio</button><button class="bt mini" data-fn="trazerClientes" title="As assinaturas ativas e em teste do Financeiro">Trazer os clientes do Financeiro</button></div>
  <table class="tab"><tr><th>Cliente</th><th>Produto</th><th>Valor</th><th>Período</th><th>Situação</th><th></th></tr>${p.negocios.map((n, i) => `<tr><td><b>${esc(n.cliente)}</b></td><td>${esc((PRODUTO_PLANO.find((x) => x[0] === n.produto) || [0, n.produto])[1])}</td>
    <td>${brl(n.valor)}${n.tipo === 'mensal' ? '/mês' : n.tipo === 'parcelas' ? ` × ${n.parcelas}` : ' único'}</td><td>${esc(n.inicio || '')}${n.fim ? ` a ${esc(n.fim)}` : ''}</td>
    <td>${n.status ? `<span class="chip ${n.status === 'fechado' ? 'pronto' : 'esperando'}">${esc(n.status)}${n.chance != null ? ` ${Math.round(n.chance * 100)}%` : ''}</span>` : '<span class="chip erro">sem status</span>'}</td>
    <td class="acoes-linha"><button class="bt mini" data-fn="negocio" data-i="${i}">Editar</button><button class="bt mini" data-fn="remover" data-lista="negocios" data-i="${i}">Tirar</button></td></tr>`).join('') || '<tr><td colspan="6">Nenhum negócio: traga os clientes do Financeiro ou cadastre.</td></tr>'}</table>
  <h2>Custos (${p.custos.length})</h2><div class="acoes" style="margin-top:0"><button class="bt pri mini" data-fn="custo">+ Custo</button></div>
  <table class="tab"><tr><th>Custo</th><th>Valor</th><th>Quando</th><th>Categoria</th><th></th></tr>${p.custos.map((c, i) => `<tr><td><b>${esc(c.item)}</b></td><td>${brl(c.valor)}</td><td>${c.frequencia === 'mensal' ? 'todo mês' : c.frequencia === 'anual' ? `por ano (${esc((c.mes || '').slice(5))})` : `uma vez (${esc(c.mes || '')})`}</td><td>${esc(c.categoria || '')}</td>
    <td class="acoes-linha"><button class="bt mini" data-fn="custo" data-i="${i}">Editar</button><button class="bt mini" data-fn="remover" data-lista="custos" data-i="${i}">Tirar</button></td></tr>`).join('') || '<tr><td colspan="5">Nenhum custo cadastrado.</td></tr>'}</table>
  <h2>Ideias de preço</h2><p class="sub" style="margin-top:0"><button class="bt mini" data-fn="simular">Simular preço</button> mensalidade, plano anual e taxa de implantação: quantos clientes pagam a conta em cada cenário.</p><div class="grade2">${pl.precos.map((x) => `<div class="cartao"><b>${esc(x.titulo)}</b><p class="sub" style="margin:4px 0 0">${esc(x.detalhe)}</p></div>`).join('')}</div>
  <p class="sub" style="margin-top:12px">Para decidir: <b>Discutir com o Financeiro</b> abre o Claude com este plano e pede caminhos, números e uma recomendação. Nada muda sem você aprovar.</p>`;
}

// ------------------------------------------------------------------ financeiro: metas e decisões (central/metas.py, central/decisoes.py)
const pctBr = (v) => `${String(Math.round((+v || 0) * 1000) / 10).replace('.', ',')}%`;
const mesAno = (m) => (m ? `${['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'][+m.slice(5, 7) - 1]}/${m.slice(2, 4)}` : '');
function ritmoFaixa(r, compacto = false) {
  if (!r.tem_meta) return '';
  const s = r.por_semana; const f = r.feito;
  const passo = (rot, alvo, feito) => `<div class="passo-ritmo"><small>${rot}</small><b>${feito != null ? `${feito}<em>/${alvo}</em>` : alvo}</b>${feito != null ? `<i style="--p:${Math.min(100, alvo ? Math.round(100 * feito / alvo) : 100)}%"></i>` : ''}</div>`;
  return `<div class="ritmo ${compacto ? 'compacto' : ''}"><div class="ritmo-cab"><b>Ritmo da semana</b> <small class="neutro">para ${r.meta} clientes até ${mesAno(r.ate)} · faltam ${r.faltam}</small>${r.atras && r.atras.length ? ` <span class="chip esperando" title="Até hoje, pelo ritmo">atrás: ${esc(r.atras.join(', '))}</span>` : r.faltam ? ' <span class="chip pronto">no ritmo</span>' : ''}</div>
    <div class="passos-ritmo">${passo('abordagens', s.abordagens, f.abordagens)}<span>→</span>${passo('respostas', s.respostas)}<span>→</span>${passo('demos', s.demos, f.demos)}<span>→</span>${passo('testes grátis', s.testes, f.testes)}<span>→</span>${passo('clientes', String(s.clientes).replace('.', ','))}</div></div>`;
}
function rumoCorpo(j, r) {
  const m = r.meta;
  const ORIGEM = { 'seus dados': 'pronto', estimativa: 'esperando', sua: '' };
  Object.assign(j.fns, {
    meta: () => dialogo(j, { titulo: 'Meta de clientes', texto: `Quantos clientes de CRM você quer ter, e até quando. A conta volta pelo funil até as abordagens por semana.${m.sugestao ? ` O seu ponto de equilíbrio (Plano do ano) é ${m.sugestao} clientes.` : ''}`,
      campos: [{ nome: 'clientes', rotulo: 'Clientes de CRM', tipo: 'numero', valor: m.meta || m.sugestao || '', obrigatorio: true, meia: true },
        { nome: 'ate', rotulo: 'Até', tipo: 'mes', valor: m.ate || '', obrigatorio: true, meia: true },
        ...Object.entries(m.taxas).map(([k, t]) => ({ nome: `taxa_${k}`, rotulo: `% de ${t.nome}`, valor: t.origem === 'sua' ? String(Math.round(t.valor * 1000) / 10).replace('.', ',') : '', meia: true,
          exemplo: `vazio = ${t.origem === 'seus dados' ? 'seus dados' : 'estimativa'} (${pctBr(t.origem === 'sua' ? r.taxas_padrao[k] : t.valor)})` }))],
      enviar: (x) => operar('meta_config', x) }),
    crescer: () => pedirEquipe(`Como Gerente, junto com o financeiro e o SDR. Meta: ${m.meta} clientes do CIELLO CRM até ${mesAno(m.ate)} (hoje ${m.ativos}, ${m.em_teste} em teste). Pela conta do OS (python central/metas.py), são ${m.por_semana.abordagens} abordagens, ${m.por_semana.demos} demos e ${m.por_semana.testes} testes grátis por semana. Monte comigo um plano de implantação de 90 dias, em etapas semanais, para chegar lá: de onde vêm os leads (Maps, anúncio, Instagram, indicação, venda para quem já é cliente), quanto tempo por dia isso pede, o que automatizar e o que parar de fazer. Leia financeiro/regras.md e respeite as regras da casa. Me pergunte antes de mudar meta, preço ou plano.`, 'Plano de crescimento'),
    discutirDecisao: ({ i, lista }) => { const x = (lista === 'abertas' ? r.abertas : r.decisoes)[+i];
      pedirEquipe(`Use o agente financeiro. Quero decidir isto sobre a Ciello: "${x.titulo}". Contexto do OS: ${x.detalhe || '(sem detalhe)'}${x.decisao ? ` Hoje a regra é: ${x.decisao}` : ''} Leia financeiro/plano.json, comercial/produtos.json e financeiro/regras.md. Me dê 2 ou 3 caminhos com os números de cada um (o que ganha, o que arrisca), a sua recomendação e uma regra curta que eu possa adotar (uma frase, para os agentes seguirem). Não decida por mim e não mude nada: quando eu escolher, registro em Financeiro → Metas e decisões.`, `Decisão · ${x.titulo.slice(0, 24)}`); },
    decidir: ({ i, lista }) => { const x = lista ? (lista === 'abertas' ? r.abertas : r.decisoes)[+i] : {};
      dialogo(j, { titulo: x.titulo ? 'Registrar decisão' : 'Nova decisão', texto: 'O que você decidir vira regra da casa: os agentes (financeiro, closer, SDR) leem antes de propor preço, desconto ou condição.',
        campos: [{ nome: 'titulo', rotulo: 'Assunto', valor: x.titulo || '', obrigatorio: true }, { nome: 'decisao', rotulo: 'O que você decidiu (uma regra curta)', tipo: 'area', valor: x.decisao || '', obrigatorio: true, exemplo: 'Ex.: site parcelado só com entrada de 30%' },
          { nome: 'revisar', rotulo: 'Rever em (opcional)', tipo: 'data', valor: x.revisar || '' }],
        extra: x.detalhe ? `<p class="sub">${esc(x.detalhe)}</p>` : '', enviar: (v) => operar('decisao_salvar', { ...v, chave: x.chave, detalhe: x.detalhe, origem: x.origem, estado: 'decidida' }) }); },
    adiar: ({ i, lista }) => { const x = (lista === 'abertas' ? r.abertas : r.decisoes)[+i];
      dialogo(j, { titulo: 'Deixar para depois', texto: x.titulo, campos: [{ nome: 'revisar', rotulo: 'Lembrar de novo em', tipo: 'data', valor: new Date(Date.now() + 30 * 864e5).toISOString().slice(0, 10) }],
        enviar: (v) => operar('decisao_salvar', { ...v, chave: x.chave, titulo: x.titulo, detalhe: x.detalhe, origem: x.origem, estado: 'adiada' }) }); },
    naoSeAplica: ({ i }) => { const x = r.abertas[+i]; rapido('decisao_salvar', { chave: x.chave, titulo: x.titulo, detalhe: x.detalhe, origem: x.origem, estado: 'descartada' }, 'Não se aplica'); },
    apagarDecisao: ({ i }) => { const x = r.decisoes[+i]; if (confirm(`Apagar a decisão "${x.titulo}"?`)) rapido('decisao_remover', { chave: x.chave }, 'Decisão apagada'); },
  });
  const metaHtml = m.tem_meta ? `<div class="kpis">${[['Meta', `${m.meta} clientes`, `até ${mesAno(m.ate)} · ${brl(m.mrr_meta)}/mês`],
      ['Hoje', `${m.ativos} clientes`, `${m.em_teste} em teste · ${brl(m.mrr_atual)}/mês`],
      ['Faltam', m.faltam, `${m.vindo_do_teste ? `${m.vindo_do_teste} ${m.vindo_do_teste > 1 ? 'devem vir' : 'deve vir'} do teste · ` : ''}${m.perdas ? `${m.perdas} cancelamento(s) no caminho` : 'sem cancelamento previsto'}`, m.faltam ? 'ruim' : 'bom'],
      ['Tempo', `${m.meses} meses`, m.meses_uteis !== m.meses ? `${m.meses_uteis} para prospectar (o teste leva 30 dias)` : '']].map(([a, b, c, k]) => `<div class="kpi"><small>${a}</small><strong>${b}</strong><em class="${k || 'neutro'}">${c}</em></div>`).join('')}</div>
    ${ritmoFaixa(m)}
    ${m.avisos.length ? `<div class="lista" style="margin-top:8px">${m.avisos.map((a) => `<div class="linha-item achado medio"><span class="chip esperando">atenção</span><div class="cresce"><small style="white-space:normal">${esc(a)}</small></div></div>`).join('')}</div>` : ''}
    <details class="taxas"><summary>De onde vêm as taxas do funil</summary><table class="tab"><tr><th>Passo</th><th>Taxa</th><th>Origem</th><th>Seus números</th></tr>${Object.values(m.taxas).map((t) => `<tr><td>${esc(t.nome)}</td><td><b>${pctBr(t.valor)}</b></td><td><span class="chip ${ORIGEM[t.origem]}">${esc(t.origem)}</span></td><td>${esc(t.dados)}</td></tr>`).join('')}</table>
      <p class="sub">A estimativa vira a sua taxa assim que houver dados suficientes (registre as abordagens, demos e testes no Comercial e no Financeiro). Para usar outro número, <a href="#" data-fn="meta">mude na meta</a>.</p></details>
    <div class="acoes"><button class="bt" data-fn="meta">Mudar meta ou taxas</button><button class="bt pri" data-fn="crescer">Montar o plano de 90 dias com a equipe</button></div>`
    : `<div class="passos"><h2>Qual é a meta?</h2><p class="sub">Diga quantos clientes de CRM quer ter e até quando. O OS faz a conta de trás para frente: quantas abordagens, demos e testes grátis por semana, e mostra no Comercial se a semana está no ritmo.${m.sugestao ? ` Pelo Plano do ano, <b>${m.sugestao} clientes</b> pagam os custos e o seu pró-labore.` : ''}</p>
      <div class="acoes" style="margin-top:0"><button class="bt pri" data-fn="meta">Definir a meta</button></div></div>`;
  const abertas = r.abertas; const rever = r.decisoes.filter((x) => x.rever_agora); const regras = r.decisoes.filter((x) => x.estado === 'decidida'); const outras = r.decisoes.filter((x) => x.estado !== 'decidida' && !x.rever_agora);
  const idx = (x) => r.decisoes.indexOf(x);
  const cartaoAberta = (x, i) => `<div class="linha-item decisao"><span class="chip ${x.origem === 'plano' ? NIVEL[x.nivel][0] : 'pronto'}">${x.origem === 'plano' ? NIVEL[x.nivel][1] : 'preço'}</span><div class="cresce"><b>${esc(x.titulo)}</b><small style="white-space:normal">${esc(x.detalhe)}</small></div>
    <div class="acoes-linha"><button class="bt mini" data-fn="discutirDecisao" data-lista="abertas" data-i="${i}" title="Abre o Claude com os caminhos e os números">Discutir</button><button class="bt mini pri" data-fn="decidir" data-lista="abertas" data-i="${i}">Decidir</button>
    <button class="bt mini" data-fn="adiar" data-lista="abertas" data-i="${i}">Depois</button><button class="bt mini" data-fn="naoSeAplica" data-i="${i}">Não se aplica</button></div></div>`;
  const cartaoDecisao = (x) => `<div class="linha-item decisao ${x.rever_agora ? 'rever' : ''}"><span class="chip ${x.estado === 'decidida' ? 'pronto' : x.estado === 'adiada' ? 'esperando' : ''}">${esc(r.estados[x.estado])}</span><div class="cresce"><b>${esc(x.titulo)}</b>
    <small style="white-space:normal">${x.decisao ? esc(x.decisao) : esc(x.detalhe || '')} · ${ddmm(x.data)}${x.revisar ? ` · rever em ${ddmm(x.revisar)}` : ''}</small></div>
    <div class="acoes-linha"><button class="bt mini" data-fn="discutirDecisao" data-lista="decisoes" data-i="${idx(x)}">Discutir</button><button class="bt mini ${x.estado === 'decidida' ? '' : 'pri'}" data-fn="decidir" data-lista="decisoes" data-i="${idx(x)}">${x.estado === 'decidida' ? 'Mudar' : 'Decidir'}</button><button class="bt mini" data-fn="apagarDecisao" data-i="${idx(x)}">Apagar</button></div></div>`;
  return `<h2 style="margin-top:4px">Meta de crescimento</h2>${metaHtml}
  <h2>Decisões${abertas.length ? ` em aberto (${abertas.length})` : ''}</h2><p class="sub" style="margin-top:0">Os furos do plano e as ideias de preço esperando a sua palavra. <b>Discutir</b> abre o Claude com caminhos e números; <b>Decidir</b> grava a regra que os agentes passam a seguir.</p>
  ${rever.length ? `<div class="lista">${rever.map(cartaoDecisao).join('')}</div>` : ''}
  <div class="lista">${abertas.map(cartaoAberta).join('') || '<p class="sub">Nada em aberto.</p>'}</div>
  <div class="acoes" style="margin-top:6px"><button class="bt mini" data-fn="decidir">+ Nova decisão</button></div>
  <h2>Regras da casa (${regras.length})</h2><p class="sub" style="margin-top:0">Ficam em financeiro/regras.md, fora do GitHub. Os agentes leem antes de propor preço, desconto ou condição.</p>
  <div class="lista">${regras.filter((x) => !x.rever_agora).map(cartaoDecisao).join('') || '<p class="sub">Nenhuma ainda. Comece pelas importantes acima.</p>'}</div>
  ${outras.length ? `<details class="taxas"><summary>Para depois e "não se aplica" (${outras.length})</summary><div class="lista">${outras.map(cartaoDecisao).join('')}</div></details>` : ''}`;
}

// ------------------------------------------------------------------ apps: comercial
const ROTULO_ETAPA = { novo: 'novo', contatado: 'contatado', respondeu: 'respondeu', demo: 'demo', proposta: 'proposta', cliente: 'cliente', perdido: 'perdido', frio: 'frio', nao_contatar: 'não contatar' };
const ORIGENS = [['instagram', 'Instagram (DM)'], ['anuncio', 'Anúncio'], ['site', 'Site'], ['indicacao', 'Indicação'], ['outro', 'Outro']];
async function renderComercial(j) {
  const d = await api('/api/app/comercial');
  const porId = Object.fromEntries(d.leads.map((l) => [l.id, l]));
  const etapaSel = (l) => `<select class="etapa" data-mudar="etapa" data-id="${l.id}" data-atual="${esc(l.etapa)}" title="Mudar a etapa">${d.etapas.map((e) => `<option value="${e}" ${e === l.etapa ? 'selected' : ''}>${esc(ROTULO_ETAPA[e] || e)}</option>`).join('')}</select>`;
  const marcar = (id, etapa, titulo, obs = '') => rapido('sdr_marcar', { id, etapa, obs }, titulo);
  j.filtro = j.filtro || { texto: '', etapa: '' };
  j.fns = {
    definirMeta: () => abrirAba('financeiro', 'rumo'),
    entrada: () => dialogo(j, { titulo: 'Lead que chegou sozinho', texto: 'Alguém chamou pela DM, anúncio, site ou indicação? Registre aqui e responda na hora: a mensagem pronta aparece embaixo, com o link do WhatsApp.',
      campos: [{ nome: 'nome', rotulo: 'Nome da pessoa', meia: true }, { nome: 'empresa', rotulo: 'Empresa', meia: true }, { nome: 'telefone', rotulo: 'WhatsApp', exemplo: '49 99999-8888', meia: true },
        { nome: 'origem', rotulo: 'Veio por', tipo: 'escolha', opcoes: ORIGENS, meia: true }, { nome: 'segmento', rotulo: 'Segmento', tipo: 'escolha', opcoes: [['', '—'], ...d.segmentos], meia: true },
        { nome: 'cidade', rotulo: 'Cidade', meia: true }, { nome: 'mensagem', rotulo: 'O que a pessoa disse', tipo: 'area' }],
      botao: 'Registrar', enviar: formOp('sdr_entrada') }),
    anotar: ({ id }) => dialogo(j, { titulo: `Anotar · ${porId[id].empresa}`, texto: esc(porId[id].obs || ''), campos: [{ nome: 'texto', rotulo: 'Anotação', tipo: 'area', obrigatorio: true, exemplo: 'liguei, pediu para retornar sexta…' }], enviar: formOp('sdr_anotar', { id }) }),
    etapa: ({ id, atual }, el) => {
      const nova = el.value;
      if (nova === 'cliente') {
        const l = porId[id];
        return dialogo(j, { titulo: `${l.empresa} fechou!`, texto: 'O que foi fechado? O cadastro vai para o Financeiro com a empresa e o WhatsApp do lead, e a etapa vira "cliente".',
          campos: [{ nome: 'oferta', rotulo: 'Produto', tipo: 'escolha', opcoes: [['crm_teste', 'CIELLO CRM · começa no teste grátis'], ['crm', 'CIELLO CRM · já paga'], ['site_avista', 'Site à vista'], ['site_parcelado', 'Site parcelado']] },
            { nome: 'valor', rotulo: 'Valor (R$, se diferente da lista)', tipo: 'numero', exemplo: 'vazio = preço de lista', meia: true }, { nome: 'dia', rotulo: 'Dia do vencimento', valor: '10', meia: true }, { nome: 'contato', rotulo: 'Contato (nome)' }],
          botao: 'Cadastrar', enviar: async ({ oferta, ...x }) => {
            const r = oferta.startsWith('site') ? await operar('fin_venda', { ...x, lead: id, forma: oferta === 'site_avista' ? 'avista' : 'parcelado' })
              : await operar('fin_cliente', { ...x, lead: id, produto: 'crm', teste: oferta === 'crm_teste' ? '30' : '0' });
            if (!r.ok) return r; const m = await operar('sdr_marcar', { id, etapa: 'cliente' }); return { ok: m.ok, saida: `${r.saida}\n${m.saida}` }; } });
      }
      if (nova === 'demo') { el.value = atual; return j.fns.agendar({ id }); }
      if (nova === 'nao_contatar' && !confirm(`${porId[id].empresa} vai para a lista de não contatar e nunca mais recebe mensagem. Confirma?`)) { el.value = atual; return null; }
      return marcar(id, nova, `Etapa: ${ROTULO_ETAPA[nova]}`);
    },
    enviei: ({ id }) => marcar(id, 'contatado', 'Contato registrado (próximo follow-up agendado)'),
    respondeu: ({ id }) => marcar(id, 'respondeu', 'Respondeu: vai para os quentes'),
    perdido: ({ id }) => marcar(id, 'perdido', 'Marcado como perdido'),
    copiar: ({ i, lista }) => copiar(d[lista][+i].mensagem),
    filtrar: (_, el) => { j.filtro[el.name] = el.value; pintarLeads(); },
    virou: ({ id, empresa }) => rapido('fin_converter', { id }, `${empresa} virou cliente`),
    agendar: ({ id }) => { const l = porId[id]; const amanha = new Date(Date.now() + 864e5); const sug = `${amanha.toISOString().slice(0, 10)}T10:00`;
      dialogo(j, { titulo: `Agendar demo · ${l.empresa}`, texto: 'Depois de salvar, a confirmação para o cliente e o link do Google Agenda aparecem aqui. No dia, o lembrete fica pronto em Comercial → Hoje.',
        campos: [{ nome: 'quando', rotulo: 'Dia e hora', tipo: 'datahora', valor: l.agenda || sug, obrigatorio: true }, { nome: 'obs', rotulo: 'Anotação', exemplo: 'equipe de 4 pessoas, usa WhatsApp Business' }],
        botao: 'Agendar', enviar: formOp('sdr_agendar', { id }) }); },
    desistiu: ({ id }) => rapido('fin_cancelar', { id, motivo: 'não continuou depois do teste grátis' }, 'Teste encerrado'),
    ofereci: ({ chave }) => { SALVO.ofertas = { ...(SALVO.ofertas || {}), [chave]: Date.now() }; salvar(); desenhar(j, true); },
    consultas: () => dialogo(j, { titulo: 'O que buscar no Google Maps', texto: 'Escolha os segmentos e as cidades. Depois clique em "Buscar no Google Maps" (leva alguns minutos e roda no seu PC).',
      campos: [{ nome: 'segmentos', rotulo: 'Segmentos', tipo: 'marcar', opcoes: d.segmentos, valor: d.segmentos.slice(0, 3) }, { nome: 'cidades', rotulo: 'Cidades', tipo: 'marcar', opcoes: d.cidades, valor: d.cidades.slice(0, 1) }],
      botao: 'Gerar as buscas', enviar: formOp('sdr_consultas') }),
    planilha: () => dialogo(j, { titulo: 'Importar planilha de leads', texto: 'Qualquer CSV com as colunas <code>title</code>, <code>phone</code>, <code>website</code>, <code>review_count</code>, <code>review_rating</code> (o formato do buscador do Google Maps). Cada empresa ganha uma nota de 0 a 100; repetidas e da lista de não contatar ficam de fora.',
      campos: [{ nome: 'arquivo', rotulo: 'Planilha (.csv)', tipo: 'arquivo', aceita: '.csv,.json', obrigatorio: true }, { nome: 'segmento', rotulo: 'Segmento (se a planilha não diz)', tipo: 'escolha', opcoes: [['', '—'], ...d.segmentos], meia: true },
        { nome: 'minimo', rotulo: 'Nota mínima', valor: '35', meia: true }],
      botao: 'Importar', enviar: ({ arquivo, ...o }) => enviarArquivo('leads', arquivo, o) }),
    crm: () => dialogo(j, { titulo: 'Exportar para o CIELLO CRM', texto: 'Gera a planilha para importar no CRM (em comercial/, fora do git).', campos: [{ nome: 'todos', rotulo: 'Incluir os leads ainda não contatados', tipo: 'sim' }], botao: 'Exportar', enviar: formOp('sdr_crm') }),
  };
  // "Já ofereci" esconde a oportunidade por 60 dias (fica guardado neste PC)
  const oferecida = (o) => Date.now() - ((SALVO.ofertas || {})[`${o.cliente_id}:${o.oferta}`] || 0) < 60 * 864e5;
  d.oportunidades = d.oportunidades.filter((o) => !oferecida(o));
  d.agenda_proximas = d.agenda.proximas; // para o botão Copiar
  const barra = `<div class="acoes topo"><button class="bt pri" data-fn="entrada">+ Lead que chegou</button><button class="bt" data-fn="planilha">Importar planilha</button><button class="bt" data-fn="crm">Exportar para o CRM</button><button class="bt" data-abrir="agente:sdr">SDR</button><button class="bt" data-abrir="agente:closer">Closer</button></div>`;
  const chipOferta = (l) => `<span class="chip ${l.oferta === 'site' ? 'oferta-site' : 'oferta-crm'}" title="O que oferecer primeiro">${l.oferta === 'site' ? 'oferta: site' : 'oferta: CRM'}</span>`;
  const msgSimples = (x, i, lista, titulo, botoes) => `<div class="cartao msg"><div class="cab"><b>${titulo}</b></div><pre class="texto-msg">${esc(x.mensagem)}</pre>
    <div class="acoes-linha">${wa(x.link)}<button class="bt" data-fn="copiar" data-lista="${lista}" data-i="${i}">Copiar</button>${botoes}</div></div>`;
  const msgCartao = (l, i, lista, extra) => `<div class="cartao msg"><div class="cab"><b>${esc(l.empresa)}</b> ${chipOferta(l)} <small class="neutro">${esc([l.segmento, l.cidade, l.pontos && `${l.pontos} pts`, extra].filter(Boolean).join(' · '))}</small>
    ${l.maps ? `<a href="${esc(l.maps)}" target="_blank" rel="noopener"><small>Maps</small></a>` : ''}</div>${l.dor_citada ? `<blockquote>“…${esc(l.dor_citada)}…”</blockquote>` : ''}
    <pre class="texto-msg">${esc(l.mensagem)}</pre><div class="acoes-linha">${l.link ? wa(l.link) : `<small class="neutro">fixo: ligar ${esc(l.telefone)}</small>`}<button class="bt" data-fn="copiar" data-lista="${lista}" data-i="${i}">Copiar</button>
    <button class="bt pri" data-fn="enviei" data-id="${l.id}">Enviei</button>${lista === 'followups' ? `<button class="bt" data-fn="respondeu" data-id="${l.id}">Respondeu</button>` : ''}<button class="bt" data-fn="perdido" data-id="${l.id}" title="Não tem interesse">Perdido</button></div></div>`;

  function linhasLeads() {
    const t = j.filtro.texto.toLowerCase();
    const lista = d.leads.filter((l) => (!j.filtro.etapa || l.etapa === j.filtro.etapa) && (!j.filtro.oferta || l.oferta === j.filtro.oferta) && (!t || [l.empresa, l.segmento, l.cidade, l.telefone, l.obs].join(' ').toLowerCase().includes(t)));
    return `<p class="sub">${lista.length} de ${d.leads.length} leads${lista.length > 300 ? ' (mostrando 300)' : ''}</p><table class="tab"><tr><th>#</th><th>Empresa</th><th>Pts</th><th>Etapa</th><th>Próximo contato</th><th></th></tr>${lista.slice(0, 300).map((l) => `<tr>
      <td>${esc(l.id)}</td><td><b>${esc(l.empresa)}</b> ${chipOferta(l)}<br><small class="neutro">${esc([l.segmento, l.cidade, l.obs].filter(Boolean).join(' · '))}</small></td><td>${esc(l.pontos)}</td><td>${etapaSel(l)}</td>
      <td>${l.proximo_contato ? `<span class="${l.proximo_contato <= d.hoje ? 'ruim' : ''}">${ddmm(l.proximo_contato)}</span>` : '—'}</td>
      <td class="acoes-linha">${l.telefone ? `<a class="bt mini" href="${esc(zap(l.telefone))}" target="_blank" rel="noopener" title="${esc(l.telefone)}">WhatsApp</a>` : ''}<button class="bt mini" data-fn="anotar" data-id="${l.id}">Anotar</button></td></tr>`).join('')}</table>`;
  }
  function pintarLeads() { const c = $('.lista-leads', j.corpo); if (c) c.innerHTML = linhasLeads(); }

  let corpo;
  if (j.aba === 'leads') {
    corpo = `<div class="filtros"><input name="texto" placeholder="Buscar empresa, cidade, telefone…" value="${esc(j.filtro.texto)}" data-mudar="filtrar">
      <select name="etapa" data-mudar="filtrar"><option value="">todas as etapas</option>${d.etapas.map((e) => `<option value="${e}" ${e === j.filtro.etapa ? 'selected' : ''}>${esc(ROTULO_ETAPA[e])}</option>`).join('')}</select>
      <select name="oferta" data-mudar="filtrar"><option value="">CRM e site</option><option value="crm" ${j.filtro.oferta === 'crm' ? 'selected' : ''}>oferta: CRM</option><option value="site" ${j.filtro.oferta === 'site' ? 'selected' : ''}>oferta: site</option></select></div><div class="lista-leads">${linhasLeads()}</div>`;
  } else if (j.aba === 'buscar') {
    corpo = `<p class="sub">Prospecção ativa sem o Claude: o buscador gratuito do Google Maps roda no seu PC, e cada empresa ganha uma nota de 0 a 100.</p>
    <div class="passos"><ol>
      <li><button class="bt ${d.tem_consultas ? '' : 'pri'}" data-fn="consultas">Escolher segmentos e cidades</button> ${d.tem_consultas ? '<span class="chip pronto">buscas prontas</span>' : ''}</li>
      <li><button class="bt ${d.tem_consultas && !d.tem_resultado ? 'pri' : ''}" data-acao="sdr_buscar" ${d.tem_consultas && d.tem_buscador ? '' : 'disabled'}>Buscar no Google Maps</button>
        ${d.tem_buscador ? '<small class="neutro">leva de 5 a 30 minutos; acompanhe na janela que abre</small>' : '<small class="ruim">buscador não instalado: rode o instalar.cmd de novo</small>'}</li>
      <li><button class="bt ${d.tem_resultado ? 'pri' : ''}" data-acao="sdr_qualificar" ${d.tem_resultado ? '' : 'disabled'}>Qualificar o resultado</button> <small class="neutro">junta as empresas novas na sua lista de leads</small></li>
      <li>Abra a aba <a data-fn="aba" data-aba="hoje" href="#">Hoje</a>: as melhores aparecem com a 1ª mensagem pronta.</li></ol></div>
    <h2>Ou importe uma planilha</h2><p class="sub">De outra ferramenta, de um evento ou de uma lista que você já tem.</p><div class="acoes" style="margin-top:0"><button class="bt" data-fn="planilha">Importar planilha de leads</button></div>`;
  } else if (!d.funil) {
    corpo = `<div class="passos"><h2>Sem leads ainda</h2><ol><li><button class="bt pri" data-fn="aba" data-aba="buscar">Buscar empresas no Google Maps</button></li>
      <li><button class="bt" data-fn="planilha">Importar uma planilha</button></li><li><button class="bt" data-fn="entrada">Registrar quem chegou sozinho</button> (DM, anúncio, indicação)</li></ol></div>`;
  } else {
    const topo = Math.max(1, d.funil.etapas[0].n);
    corpo = `${d.ritmo && d.ritmo.tem_meta ? ritmoFaixa(d.ritmo, true) : `<p class="sub">Sem meta de clientes ainda: <a href="#" data-fn="definirMeta">defina a meta</a> e o OS mostra aqui o ritmo da semana.</p>`}<div class="grade2"><div class="cartao"><h2 style="margin-top:0">Funil</h2><div class="funil">${d.funil.etapas.map((e, i) => `<div><span>${esc(e.etapa)}</span><i style="width:${Math.max(2, 100 * e.n / topo)}%"></i><b>${e.n}</b><small>${i && d.funil.etapas[i - 1].n ? Math.round(100 * e.n / d.funil.etapas[i - 1].n) + '%' : ''}</small></div>`).join('')}</div></div>
    <div class="cartao"><h2 style="margin-top:0">Quentes · responder hoje</h2><div class="lista">${d.quentes.map((l) => `<div class="linha-item"><div class="cresce"><b>${esc(l.empresa)}</b><small>${esc([l.segmento, l.cidade, l.obs].filter(Boolean).join(' · '))}</small></div>
      ${l.telefone ? `<a class="bt mini wa" href="${esc(zap(l.telefone))}" target="_blank" rel="noopener">WhatsApp</a>` : ''}<button class="bt mini" data-fn="agendar" data-id="${l.id}">${l.agenda ? `Demo ${ddmm(l.agenda)} ${l.agenda.slice(11, 16)}` : 'Agendar demo'}</button>${etapaSel(l)}</div>`).join('') || '<p class="sub">Ninguém esperando resposta.</p>'}</div></div></div>
    ${d.agenda.proximas.length ? `<h2>Agenda de demos (${d.agenda.proximas.length})</h2>${d.agenda.proximas.map((a, i) => msgSimples(a, i, 'agenda_proximas',
      `${esc(a.empresa)} <span class="chip ${a.dias === 0 ? 'erro' : 'esperando'}">${a.dias === 0 ? 'hoje' : a.dias === 1 ? 'amanhã' : ddmm(a.quando)} às ${esc(a.quando.slice(11, 16))}</span> <small class="neutro">${a.dias === 0 ? 'lembrete' : 'confirmação'}</small>`,
      `<a class="bt" href="${esc(a.agenda_google)}" target="_blank" rel="noopener">Google Agenda</a><button class="bt" data-fn="agendar" data-id="${a.id}">Remarcar</button>`)).join('')}` : ''}
    ${d.agenda.sem_desfecho.length ? `<h2>Como foram as demos? (${d.agenda.sem_desfecho.length})</h2><div class="lista">${d.agenda.sem_desfecho.map((a) => `<div class="linha-item"><div class="cresce"><b>${esc(a.empresa)}</b><small>demo em ${ddmm(a.quando)} às ${esc(a.quando.slice(11, 16))}</small></div>${etapaSel(porId[a.id] || a)}</div>`).join('')}</div>` : ''}
    ${d.testes.length ? `<h2>Teste grátis acabando (${d.testes.length})</h2>${d.testes.map((t, i) => msgSimples(t, i, 'testes', `${esc(t.empresa)} <span class="chip ${t.dias <= 2 ? 'erro' : 'esperando'}">${t.dias < 0 ? `acabou há ${-t.dias} dia(s)` : t.dias === 0 ? 'acaba hoje' : `faltam ${t.dias} dias`}</span> <small class="neutro">${brl(t.valor)}/mês</small>`,
      `<button class="bt pri" data-fn="virou" data-id="${t.cliente_id}" data-empresa="${esc(t.empresa)}">Virou cliente</button><button class="bt" data-fn="desistiu" data-id="${t.cliente_id}">Desistiu</button>`)).join('')}` : ''}
    <h2>Follow-ups de hoje (${d.followups.length})</h2>${d.followups.map((l, i) => msgCartao(l, i, 'followups', `tentativa ${+l.tentativas + 1}`)).join('') || '<p class="sub">Nenhum follow-up para hoje.</p>'}
    <h2>Abordar · melhores leads novos (${d.abordar.length})</h2>${d.abordar.map((l, i) => msgCartao(l, i, 'abordar')).join('') || '<p class="sub">Fila vazia: busque mais leads na aba Buscar leads.</p>'}
    ${d.oportunidades.length ? `<h2>Vender para quem já é cliente (${d.oportunidades.length})</h2><p class="sub">Quem já confia na Ciello compra o 2º produto mais fácil do que um lead novo.</p>${d.oportunidades.map((o, i) => msgSimples(o, i, 'oportunidades', `${esc(o.empresa)} <span class="chip ${o.oferta === 'site' ? 'oferta-site' : 'oferta-crm'}">oferta: ${o.oferta === 'site' ? 'site' : 'CRM'}</span> <small class="neutro">${esc(o.porque)}</small>`, `<button class="bt" data-fn="ofereci" data-chave="${o.cliente_id}:${o.oferta}" title="Some da lista por 60 dias">Já ofereci</button>`)).join('')}` : ''}`;
  }
  j.corpo.innerHTML = `<div class="pagina"><h1>Comercial</h1><p class="sub">${d.funil ? `${num(d.funil.total)} leads · ${num(d.funil.perdidos)} perdidos ou frios` : 'Prospecção, follow-up e fechamento do CIELLO CRM.'}</p>${SEM_CLAUDE}${barra}
  ${abas(j, [['hoje', 'Hoje', d.followups.length + d.quentes.length + d.testes.length + d.agenda.proximas.length || ''], ['leads', 'Leads', d.leads.length], ['buscar', 'Buscar leads']])}${corpo}</div>`;
}

// ------------------------------------------------------------------ apps: conteúdo
async function renderConteudo(j) {
  const d = await api('/api/app/conteudo'); const i = d.instagram;
  const kpi = (r, v, e = '', c = 'neutro') => `<div class="kpi"><small>${r}</small><strong>${v}</strong><em class="${c}">${e}</em></div>`;
  const delta = i && i.seguidores_antes != null ? i.seguidores - i.seguidores_antes : null;
  const COLS = [['gancho', 'Gancho (início da fala)'], ['data', 'Data'], ['views', 'Views'], ['alcance', 'Alcance'], ['salvamentos', 'Salv.'], ['compartilhamentos', 'Comp.'], ['comentarios', 'Coment.'], ['tempo_medio_s', 'Tempo (s)']];
  const linhaReel = () => `<tr>${COLS.map(([k]) => `<td><input name="r-${k}" ${k === 'data' ? 'type="date"' : ''} ${k === 'gancho' ? '' : 'inputmode="decimal"'}></td>`).join('')}</tr>`;
  j.fns = {
    retrato: () => {
      const el = dialogo(j, { titulo: 'Anotar números do Instagram', texto: 'Sem o Claude para puxar do Metricool? Copie os números do app do Instagram (Painel profissional → Insights, últimos 30 dias). O relatório semanal e o Bom dia usam este retrato.',
        campos: [{ nome: 'data', rotulo: 'Data do retrato', tipo: 'data', valor: hojeISO(), meia: true }, { nome: 'seguidores', rotulo: 'Seguidores', tipo: 'numero', obrigatorio: true, valor: i ? i.seguidores : '', meia: true },
          { nome: 'alcance', rotulo: 'Contas alcançadas (30 dias)', tipo: 'numero', meia: true }, { nome: 'contas_engajadas', rotulo: 'Contas com engajamento', tipo: 'numero', meia: true }, { nome: 'posts', rotulo: 'Posts no período', tipo: 'numero', meia: true }],
        extra: `<h3>Reels do período (opcional)</h3><div class="tab-rolagem"><table class="tab reels-form"><tr>${COLS.map(([, r]) => `<th>${r}</th>`).join('')}</tr>${linhaReel().repeat(3)}</table></div><button type="button" class="bt mini mais-reel">+ reel</button>`,
        botao: 'Salvar retrato',
        enviar: (dados, form) => {
          const reels = [...form.querySelectorAll('.reels-form tr')].slice(1).map((tr) => Object.fromEntries(COLS.map(([k]) => [k, $(`[name="r-${k}"]`, tr).value.trim()]))).filter((r) => r.gancho);
          return operar('ig_retrato', { ...dados, reels });
        } });
      $('.mais-reel', el).onclick = () => $('.reels-form', el).insertAdjacentHTML('beforeend', linhaReel());
    },
    legenda: async ({ post }) => {
      const q = d.quadro.find((x) => x.post === post);
      let texto = q.legenda;
      if (!texto) { const r = await operar('cont_legenda', { post }); if (!r.ok) return aviso({ titulo: 'Não deu', texto: r.saida, cor: '#C8442F' }); texto = r.legenda; }
      dialogo(j, { titulo: `Legenda · ${q.titulo}`, texto: 'Rascunho feito das falas do roteiro: gancho na 1ª linha, valor, chamada e hashtags. Ajuste no seu jeito e salve.',
        campos: [{ nome: 'texto', rotulo: 'Legenda', tipo: 'area', valor: texto }], botao: 'Salvar legenda',
        extra: '<div class="acoes-linha" style="margin-top:8px"><button type="button" class="bt mini copiar-legenda">Copiar</button><small class="neutro">até 2.200 caracteres</small></div>',
        enviar: ({ texto: t }) => operar('cont_legenda_salvar', { post, texto: t }) });
      $('.dialogo .caixa-dialogo textarea', j.el).rows = 12;
      $('.dialogo .copiar-legenda', j.el).onclick = () => copiar($('.dialogo textarea', j.el).value);
    },
    agendei: ({ post }) => { const q = d.quadro.find((x) => x.post === post); dialogo(j, { titulo: `Agendado · ${q.titulo}`, texto: 'Registre aqui quando você agendou o post no Metricool (ou publicou direto no Instagram). Fica no historico.md.',
      campos: [{ nome: 'quando', rotulo: 'Data e hora do post', valor: `${q.data.slice(8, 10)}/${q.data.slice(5, 7)} 10h`, meia: true }, { nome: 'publicado', rotulo: 'Situação', tipo: 'escolha', opcoes: [['', 'Agendado'], ['sim', 'Já publicado']], meia: true }],
      botao: 'Registrar', enviar: (x) => operar('cont_agendado', { post, quando: x.quando, publicado: !!x.publicado }) }); },
    postar: ({ post }) => {
      const q = d.quadro.find((x) => x.post === post);
      const video = `/midia/final/${encodeURIComponent(post)}.mp4`; const capa = q.etapas.capa ? `/midia/capas/${encodeURIComponent(post)}.jpg` : '';
      dialogo(j, { titulo: `Postar · ${q.titulo}`, texto: 'Tudo o que o Metricool (ou o Instagram) pede num lugar só: baixe o vídeo e a capa, copie a legenda e agende no horário. Depois registre aqui.',
        campos: [{ nome: 'quando', rotulo: 'Data e hora do post', valor: `${ddmm(q.data)} 10h`, meia: true }, { nome: 'publicado', rotulo: 'Situação', tipo: 'escolha', opcoes: [['', 'Agendei'], ['sim', 'Já publiquei']], meia: true }],
        extra: `<div class="pacote-post"><div class="midias"><video src="${video}" controls preload="metadata"></video>${capa ? `<img src="${capa}" alt="capa">` : ''}</div>
          <div class="cresce"><div class="acoes-linha"><a class="bt mini" href="${video}" download>Baixar vídeo</a>${capa ? `<a class="bt mini" href="${capa}" download>Baixar capa</a>` : '<small class="ruim">sem capa ainda</small>'}</div>
          ${q.legenda ? `<pre class="texto-msg legenda-pacote">${esc(q.legenda)}</pre><button type="button" class="bt mini copiar-pacote">Copiar legenda</button>` : '<p class="sub">Sem legenda ainda: <button type="button" class="bt mini gerar-legenda">Gerar legenda</button></p>'}
          <p class="sub">Prefere que a equipe agende? <button type="button" class="bt mini agendar-claude">Agendar no Metricool com o Claude</button> (ele te mostra antes e só agenda com o seu ok).</p></div></div>`,
        botao: 'Registrar', enviar: (x) => operar('cont_agendado', { post, quando: x.quando, publicado: !!x.publicado }) });
      const dlg = $('.dialogo', j.el);
      const cp = $('.copiar-pacote', dlg); if (cp) cp.onclick = () => copiar(q.legenda);
      const gl = $('.gerar-legenda', dlg); if (gl) gl.onclick = () => { $('.cancelar', dlg).click(); j.fns.legenda({ post }); };
      $('.agendar-claude', dlg).onclick = () => { $('.cancelar', dlg).click(); pedirEquipe(`Use o agente postagem: agende o post ${post} ("${q.titulo}") no Metricool para ${ddmm(q.data)} às 10:00 (America/Sao_Paulo), como Reel do Instagram, com o vídeo midia/final/${post}.mp4, ${capa ? `a capa midia/capas/${post}.jpg` : 'sem capa (avise)'} e a legenda do roteiro (roteiros/${post}.json). Siga o AGENTE.md para a URL do vídeo. Antes de criar, me mostre o resumo (horário, legenda, links) e espere o meu ok. Depois registre no historico.md.`, `Postar ${ddmm(q.data)}`); };
    },
    produzir: ({ post }) => { const q = d.quadro.find((x) => x.post === post); pedirEquipe(`Termine o post ${post} ("${q.titulo}", vai ao ar em ${ddmm(q.data)}). Falta: ${q.falta.map((e) => (d.etapas.find((x) => x[0] === e) || [e, e])[1]).join(', ')}. Siga o AGENTE.md (narração com a voz do Estúdio de Voz, vídeo final, capa, legenda) e me mostre o vídeo e a legenda antes de agendar. Só agende no Metricool depois que eu aprovar.`, `Post ${ddmm(q.data)}`); },
  };
  const etapaChip = (q, e, rot) => `<span class="etapa-post ${q.etapas[e] ? 'feita' : q.proximo === e ? 'proxima' : ''}" title="${esc(rot)}${q.etapas[e] ? ': feito' : q.proximo === e ? ': próximo passo' : ''}">${q.etapas[e] ? '✓' : ''} ${esc(rot)}</span>`;
  const quando = (q) => (q.dias === 0 ? 'hoje' : q.dias === 1 ? 'amanhã' : q.dias < 0 ? `há ${-q.dias} dias` : `em ${q.dias} dias`);
  const producao = `${d.alertas.length ? `<div class="lista" style="margin-top:12px">${d.alertas.map((a) => `<div class="linha-item achado alto">${esc(a)}</div>`).join('')}</div>` : ''}
  <h2>Próximos posts</h2><div class="quadro-posts">${d.quadro.filter((q) => q.dias >= 0).map((q) => cartaoPost(q)).join('') || '<div class="vazio">Nenhum post na agenda. Rode a esteira <b>Semana de conteúdo</b> em Objetivos.</div>'}</div>
  ${d.quadro.some((q) => q.dias < 0) ? `<details class="passados"><summary>Posts passados (${d.quadro.filter((q) => q.dias < 0).length})</summary><div class="quadro-posts">${d.quadro.filter((q) => q.dias < 0).reverse().map((q) => cartaoPost(q)).join('')}</div></details>` : ''}`;
  function cartaoPost(q) { return `<div class="cartao post-linha ${q.pronto ? 'pronto' : ''}">
    <div class="post-cab"><b>${ddmm(q.data)}</b> <small class="${q.dias >= 0 && q.dias <= 2 && !q.pronto ? 'ruim' : 'neutro'}">${quando(q)}</small> <span>${esc(q.titulo)}</span>${q.status_historico ? `<small class="neutro" title="historico.md">· ${esc(q.status_historico.slice(0, 60))}</small>` : ''}</div>
    <div class="etapas-post">${d.etapas.map(([e, r]) => etapaChip(q, e, r)).join('<i>›</i>')}</div>
    <div class="acoes-linha">${q.pronto ? '<span class="chip pronto">pronto e agendado</span>' : `<small class="neutro">Próximo: <b>${esc((d.etapas.find((x) => x[0] === q.proximo) || ['', ''])[1])}</b> com ${esc(nome(q.dono))}</small>`}
      <button class="bt mini" data-fn="legenda" data-post="${esc(q.post)}">${q.etapas.legenda ? 'Ver legenda' : 'Gerar legenda'}</button>
      ${!q.etapas.agendado ? (q.etapas.final && q.dias >= 0 ? `<button class="bt mini pri" data-fn="postar" data-post="${esc(q.post)}" title="Vídeo, capa, legenda e horário num lugar só">Postar</button>` : `<button class="bt mini" data-fn="agendei" data-post="${esc(q.post)}">${q.dias < 0 ? 'Foi publicado?' : 'Já agendei'}</button>`) : ''}
      ${!q.etapas.final && q.dias >= 0 ? `<button class="bt mini" data-abrir="video" title="Gera o vídeo no seu PC, sem o Claude">Gerar no Estúdio</button>` : ''}
      ${!q.pronto && q.dias >= 0 ? `<button class="bt mini ${q.etapas.final ? '' : 'pri'}" data-fn="produzir" data-post="${esc(q.post)}" title="Abre o Claude com a equipe de conteúdo">Terminar com a equipe</button>` : ''}</div></div>`; }
  const rodapeProducao = `<p class="sub">Próximos horários livres (seg, qua e sex às 10h): ${d.horarios.map((h) => ddmm(h)).join(', ')}. Para criar posts novos: <a data-abrir="objetivos" style="cursor:pointer;color:var(--azul-claro)">Objetivos → Semana de conteúdo</a>.</p>`;
  const analise = `<div class="acoes" style="margin-top:12px"><button class="bt pri" data-acao="relatorio">${icone('play')} Gerar o relatório da semana</button><button class="bt" data-fn="retrato">Anotar números novos</button>
    <button class="bt" data-fn="analisar" title="Abre o Claude com o analista">Discutir com o Analista</button></div>
    ${d.relatorio ? `<p class="sub">${esc(d.relatorio.arquivo)} · o que mudar está no fim.</p><div class="cartao md">${md(d.relatorio.texto)}</div>` : '<div class="vazio">Sem relatório ainda. Anote os números do Instagram e clique em <b>Gerar o relatório da semana</b>.</div>'}`;
  j.fns.analisar = () => pedirEquipe('Use o analista: leia o último retrato em metricas/ e o relatório da semana. Me diga em 5 linhas o que está funcionando, o que parar de fazer e qual gancho testar nos próximos 3 reels, com base nos números (retenção, salvamentos, compartilhamentos) e na biblioteca de ganchos (python central/ganchos.py ranking).', 'Analista');
  const insta = `${i ? `<div class="kpis">${kpi('Seguidores', num(i.seguidores), delta != null ? `${delta >= 0 ? '+' : ''}${delta} na semana` : '', delta >= 0 ? 'bom' : 'ruim')}${kpi('Alcance 30 dias', num(i.alcance))}
  ${kpi('Tempo médio no reel', `${String(i.tempo_medio).replace('.', ',')}s`, 'meta 6s', i.tempo_medio >= 6 ? 'bom' : 'ruim')}${kpi('Salvamentos', `${String(i.salvamentos_pct).replace('.', ',')}%`, 'meta 1%', i.salvamentos_pct >= 1 ? 'bom' : 'ruim')}</div>` : '<div class="vazio">Sem retrato do Instagram ainda. Clique em <b>Anotar números do Instagram</b> (ou rode /segunda no Claude Code).</div>'}
  <h2>Posts · próximos e recentes</h2><div class="posts">${d.posts.map((p) => `<div class="post">${p.capa ? `<img src="${esc(p.capa)}" alt="" loading="lazy">` : '<div class="sem-capa"></div>'}<div><b>${ddmm(p.data)}</b>${esc(p.titulo)}<br>${p.final ? '<span class="chip pronto">vídeo pronto</span>' : '<span class="chip esperando">sem vídeo final</span>'}</div></div>`).join('')}</div>
  ${i && i.reels.length ? `<h2>Reels que mais alcançaram</h2><table class="tab"><tr><th>Data</th><th>Gancho</th><th>Alcance</th><th>Tempo</th></tr>${i.reels.map((r) => `<tr><td>${ddmm(r.data)}</td><td>${esc(r.gancho)}</td><td>${num(r.alcance)}</td><td>${String(r.tempo_medio_s ?? '').replace('.', ',')}s</td></tr>`).join('')}</table>` : ''}
  <div class="acoes"><button class="bt" data-acao="ganchos">Ranking de ganchos</button><button class="bt" data-abrir="agente:produtor-video">Produtor de vídeo</button><button class="bt" data-abrir="agente:postagem">Postagem</button></div>`;
  j.corpo.innerHTML = `<div class="pagina"><h1>Conteúdo e Instagram</h1><p class="sub">@ciellotec${i ? ` · retrato de ${ddmm(i.data)}` : ''}</p>${SEM_CLAUDE}
  <div class="acoes topo"><button class="bt pri" data-fn="retrato">Anotar números do Instagram</button><button class="bt" data-acao="relatorio">Relatório semanal</button><button class="bt" data-abrir="voz">Estúdio de Voz</button></div>
  ${abas(j, [['producao', 'Produção', d.quadro.filter((q) => !q.pronto && q.dias >= 0).length || ''], ['instagram', 'Instagram'], ['analise', 'Análise']])}${j.aba === 'instagram' ? insta : j.aba === 'analise' ? analise : producao + rodapeProducao}</div>`;
}

// ------------------------------------------------------------------ apps: conexões (central/conexoes.py)
const ESTADO_ENVIO = { na_fila: ['', 'na fila'], aguardando_aprovacao: ['esperando', 'esperando você'], aprovado: ['pronto', 'aprovado'], agendado: ['trabalhando', 'agendado'],
  publicado: ['trabalhando', 'publicado'], erro: ['erro', 'erro'], segurado: ['parado', 'segurado'], perdido: ['erro', 'passou da hora'], cancelado: ['parado', 'cancelado'],
  'na fila': ['', 'na fila'], 'em produção': ['esperando', 'em produção'], '—': ['parado', '—'], 'sem registro': ['parado', 'sem registro'] };
const chipEnvio = (estado, titulo = '') => { const [c, r] = ESTADO_ENVIO[estado] || ['', estado]; return `<span class="chip ${c}" title="${esc(titulo)}">${esc(r)}</span>`; };
const quandoBr = (iso) => (iso ? `${iso.slice(8, 10)}/${iso.slice(5, 7)} ${iso.slice(11, 16)}` : '');
async function renderConexoes(j) {
  const d = await api('/api/app/conexoes');
  const porId = Object.fromEntries(d.provedores.map((p) => [p.id, p]));
  j.fns = {
    conectar: ({ id }) => { const p = porId[id];
      dialogo(j, { titulo: `Conectar · ${p.nome}`, texto: `${p.ajuda}${p.limite ? ` Atenção: ${p.limite}` : ''}`,
        campos: p.campos.map((c) => ({ nome: c.nome, rotulo: c.rotulo, valor: c.segredo ? '' : (p.preenchidos[c.nome] || c.padrao || ''), dica: c.ajuda || '',
          exemplo: c.segredo && p.preenchidos[c.nome] ? `guardado (${p.preenchidos[c.nome]}): vazio mantém` : '', obrigatorio: !p.preenchidos[c.nome] && !c.padrao })),
        botao: p.oauth ? 'Salvar' : 'Salvar e checar', extra: p.oauth ? `<p class="sub">Depois de salvar, clique em <b>Entrar</b> no cartão. Endereço de retorno para cadastrar no app: <code>${esc(location.origin)}/oauth/${esc(id)}</code></p>` : '',
        enviar: (x) => operar('conexao_salvar', { ...x, provedor: id }) }); },
    entrar: async ({ id }) => { const r = await operar('oauth_inicio', { provedor: id });
      if (!r.ok) return aviso({ titulo: 'Não deu', texto: r.saida, cor: '#C8442F' });
      window.open(r.url, '_blank', 'noopener'); aviso({ titulo: 'Login aberto no navegador', texto: 'Entre na conta e autorize. Depois volte aqui e clique em Checar.', cor: '#3A5582' }); },
    checar: ({ id }) => rapido('conexao_checar', { provedor: id }, 'Conexão checada'),
    desconectar: ({ id }) => { if (confirm(`Desconectar ${porId[id].nome}? A senha sai do cofre. O histórico (posts, números e comentários) continua guardado no seu PC.`)) rapido('conexao_desconectar', { provedor: id }, 'Desconectado'); },
    exportar: () => rapido('social_exportar', {}, 'Histórico exportado'),
  };
  j.fns.mudarRede = ({ rede, campo }, el) => { operar('conexao_rede', campo === 'ativa' ? { rede, ativa: el.value === 'sim' } : { rede, via: el.value }).then((r) => { if (!r.ok) aviso({ titulo: 'Não deu', texto: r.saida, cor: '#C8442F' }); }); };
  const situacao = (p) => { const e = p.estado || {};
    if (!e.conectado && !(p.id === 'claude')) return '<span class="chip parado">não conectado</span>';
    if (e.ok === false) return `<span class="chip erro" title="${esc(e.mensagem || '')}">caiu${e.caiu_em ? ` em ${quandoBr(e.caiu_em)}` : ''}</span>`;
    if (e.ok) return `<span class="chip trabalhando">conectado</span>`;
    return '<span class="chip">não checado</span>'; };
  const redes = Object.entries(d.redes).map(([rede, r]) => {
    const opcoes = d.provedores.filter((p) => p.publica.includes(rede));
    return `<tr><td><b>${esc(d.nomes_redes[rede])}</b></td><td><select data-mudar="mudarRede" data-rede="${rede}" data-campo="ativa"><option value="sim" ${r.ativa ? 'selected' : ''}>ligada</option><option value="nao" ${r.ativa ? '' : 'selected'}>desligada</option></select></td>
      <td><select data-mudar="mudarRede" data-rede="${rede}" data-campo="via"><option value="">— escolha —</option>${opcoes.map((p) => `<option value="${p.id}" ${r.via === p.id ? 'selected' : ''}>${esc(p.nome)}</option>`).join('')}</select></td>
      <td>${r.via ? situacao(porId[r.via]) : '<small class="neutro">sem provedor: não publica</small>'}</td></tr>`; }).join('');
  const cartao = (p) => { const e = p.estado || {}; const h = p.historico || {};
    return `<div class="cartao conexao"><div class="cab-conexao"><b>${esc(p.nome)}</b>${situacao(p)}${e.conta ? `<small class="neutro">${esc(e.conta)}</small>` : ''}</div>
      <p class="sub" style="margin:4px 0">${esc(p.ajuda)}${p.limite ? ` <span class="neutro">· ${esc(p.limite)}</span>` : ''}</p>
      ${e.ok === false ? `<div class="linha-item achado alto"><small style="white-space:normal">${esc(e.mensagem || '')}</small></div>` : ''}
      <small class="neutro">Redes: ${p.redes.map((r) => d.nomes_redes[r]).join(', ')}${e.ultima_checagem ? ` · checado em ${quandoBr(e.ultima_checagem)}` : ''}
        · guardado no PC: ${h.publicacoes || 0} publicações, ${h.comentarios || 0} comentários${h.desde ? ` desde ${ddmm(h.desde)}` : ''}${h.ultima_sync ? ` · última sincronização ${quandoBr(h.ultima_sync)}` : ''}</small>
      <div class="acoes-linha" style="margin-top:8px">${p.campos.length ? `<button class="bt mini ${e.conectado ? '' : 'pri'}" data-fn="conectar" data-id="${p.id}">${e.conectado ? 'Editar' : 'Conectar'}</button>` : ''}
        ${p.oauth ? `<button class="bt mini ${p.logado ? '' : 'pri'}" data-fn="entrar" data-id="${p.id}">${p.logado ? 'Entrar de novo' : `Entrar com ${p.id === 'youtube' ? 'o Google' : 'o TikTok'}`}</button>` : ''}
        <button class="bt mini" data-fn="checar" data-id="${p.id}">Checar agora</button>${e.conectado && p.campos.length ? `<button class="bt mini" data-fn="desconectar" data-id="${p.id}">Desconectar</button>` : ''}</div></div>`; };
  j.corpo.innerHTML = `<div class="pagina"><h1>Conexões</h1><p class="sub">Metricool, Instagram, YouTube e TikTok. Tudo o que vem deles é copiado para o seu PC: se um provedor cair ou for desconectado, você não perde histórico nem trabalho, e os posts esperam na fila até a conexão voltar.</p>
  ${d.cofre_protegido ? '' : '<div class="faixa">Neste sistema as senhas ficam só codificadas (sem a proteção do Windows). No seu PC com Windows elas são cifradas.</div>'}
  <h2>Por onde cada rede publica</h2><table class="tab"><tr><th>Rede</th><th>Piloto</th><th>Publica por</th><th>Situação</th></tr>${redes}</table>
  <h2>Provedores</h2><div class="grade2">${d.provedores.map(cartao).join('')}</div>
  <div class="acoes"><button class="bt pri" data-acao="sincronizar">Sincronizar agora</button><button class="bt" data-fn="exportar" title="Tudo em CSV, em estado/exportacao">Exportar histórico (CSV)</button></div></div>`;
}

// ------------------------------------------------------------------ apps: rede social (piloto, calendário, comentários, resultados)
const CATEGORIA = { lead: ['erro', 'quer comprar'], pergunta: ['esperando', 'pergunta'], elogio: ['trabalhando', 'elogio'], outro: ['', 'outro'], spam: ['parado', 'spam'] };
const VEREDITO = { acima: ['trabalhando', 'acima da média'], 'na média': ['', 'na média'], abaixo: ['erro', 'abaixo da média'] };
async function renderRedes(j) {
  const d = await api('/api/app/redes'); const P = d.piloto; const C = j.proximoMes ? d.calendario_proximo : d.calendario; const c = P.config;
  const nomeRede = (r) => d.nomes_redes[r] || r;
  j.fns = {
    modo: ({ m }) => rapido('piloto_config', { modo: m }, 'Piloto'),
    ajustes: () => dialogo(j, { titulo: 'Ajustes do piloto', texto: 'O piloto roda de hora em hora pelo Agendador do Windows (agendar.cmd). Estes ajustes valem já na próxima rodada.',
      campos: [{ nome: 'antecedencia_dias', rotulo: 'Produzir com quantos dias de antecedência', tipo: 'numero', valor: c.antecedencia_dias, meia: true },
        { nome: 'envio_antecedencia_h', rotulo: 'Agendar no provedor quantas horas antes', tipo: 'numero', valor: c.envio_antecedencia_h, meia: true, dica: 'até essa hora dá para Segurar o post' },
        { nome: 'responder', rotulo: 'Comentários', tipo: 'escolha', opcoes: [['elogios_e_faq', 'Responder elogios e perguntas do FAQ sozinho'], ['elogios', 'Responder só elogios'], ['nunca', 'Nunca responder sozinho']], valor: c.responder },
        { nome: 'modelo_video', rotulo: 'Modelo do vídeo', tipo: 'escolha', opcoes: [['escuro', 'Escuro'], ['claro', 'Claro']], valor: c.modelo_video, meia: true }],
      enviar: (x) => operar('piloto_config', x) }),
    segurar: ({ post, rede }) => rapido('envio_segurar', { post, rede }, 'Segurado'),
    aprovar: ({ post, rede }) => rapido('envio_aprovar', { post, rede }, 'Aprovado'),
    tentar: ({ post, rede }) => rapido('envio_tentar', { post, rede }, 'De volta à fila'),
    calConfig: () => { const DIAS = ['seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom'];
      dialogo(j, { titulo: 'Calendário', texto: 'Em quais dias sai post e o horário de cada rede. O mesmo vídeo vai para todas as redes ligadas.',
        campos: [{ nome: 'dias', rotulo: 'Dias com post', tipo: 'marcar', opcoes: DIAS, valor: C.config.dias.map((x) => DIAS[x]) },
          ...Object.keys(d.nomes_redes).map((r) => ({ nome: `hora_${r}`, rotulo: `Horário · ${nomeRede(r)}`, valor: C.config.horarios[r], meia: true })),
          { nome: 'limite_metricool', rotulo: 'Posts por mês no seu plano do Metricool', tipo: 'numero', valor: C.config.limite_metricool, meia: true, dica: 'grátis: 20 · 0 = sem limite' }],
        enviar: (x) => operar('calendario_config', { ...x, dias: x.dias.map((s) => DIAS.indexOf(s)) }) }); },
    responder: ({ i }) => { const k = d.comentarios[+i]; const t = $(`.resp-${i}`, j.corpo).value.trim(); rapido('comentario_responder', { rede: k.rede, id: k.id_ext, texto: t }, 'Comentário'); },
    marcarCom: ({ i, estado, lista }) => { const k = d[lista || 'comentarios'][+i]; rapido('comentario_marcar', { rede: k.rede, id: k.id_ext, estado }, 'Comentário'); },
    copiarResp: ({ i }) => copiar(d.aguardando[+i].resposta),
  };
  const caidas = P.caidas.length ? `<div class="lista">${P.caidas.map((x) => `<div class="linha-item achado alto"><span class="chip erro">caiu</span><div class="cresce"><b>${esc(x.nome)}</b><small style="white-space:normal">${esc(x.mensagem)} · os posts dessa rede esperam na fila</small></div><button class="bt mini" data-abrir="conexoes">Conexões</button></div>`).join('')}</div>` : '';
  const semRede = !Object.values(d.redes).some((r) => r.ativa && r.via);
  let corpo;
  if (j.aba === 'calendario') {
    const prev = C.previsao;
    j.fns.trocarMes = () => { j.proximoMes = !j.proximoMes; desenhar(j, true); };
    corpo = `<div class="acoes" style="margin-top:0"><button class="bt mini" data-fn="trocarMes">${j.proximoMes ? '◀ Este mês' : 'Próximo mês ▶'}</button><button class="bt mini" data-fn="calConfig">Dias e horários</button></div>
    <div class="kpis">${Object.entries(prev.redes).map(([r, p]) => `<div class="kpi"><small>${esc(nomeRede(r))} · ${p.posts_planejados} posts</small><strong>${p.views_previstas != null ? num(p.views_previstas) : '—'}</strong>
      <em class="neutro">${p.views_previstas != null ? `views previstas (mediana ${num(p.mediana_views)}/post)` : 'sem histórico para prever'}${p.seguidores_fim_mes != null ? ` · ${num(p.seguidores_fim_mes)} seguidores no fim do mês` : ''}</em></div>`).join('') || '<div class="vazio">Ligue uma rede em Conexões.</div>'}
      ${prev.limite_metricool ? `<div class="kpi"><small>Metricool no mês</small><strong>${prev.posts_metricool} de ${prev.limite_metricool}</strong><em class="${prev.posts_metricool > prev.limite_metricool ? 'ruim' : 'bom'}">posts pelo seu plano</em></div>` : ''}</div>
    ${prev.avisos.length ? `<div class="lista" style="margin-top:8px">${prev.avisos.map((a) => `<div class="linha-item achado medio"><small style="white-space:normal">${esc(a)}</small></div>`).join('')}</div>` : ''}
    <h2>${['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'][C.mes - 1]} de ${C.ano}</h2>
    <table class="tab cal"><tr><th>Dia</th><th>Post</th>${Object.keys(C.redes).map((r) => `<th>${esc(nomeRede(r))}</th>`).join('')}</tr>${C.dias.map((x) => `<tr class="${x.passado ? 'passado' : ''}">
      <td><b>${ddmm(x.data)}</b> <small class="neutro">${x.dia_semana}</small></td>
      <td>${x.post ? `${esc(x.post.titulo)} <span class="chip">${esc(C.pilares[x.post.pilar] || x.post.pilar)}</span>${x.post.pronto || x.post.final ? '' : ` <small class="neutro">falta: ${esc(x.post.falta.map((e) => C.etapas[e] || e).join(', '))}</small>`}`
        : `<small class="neutro">vazio${x.sugestao ? ` · sugestão: ${esc(C.pilares[x.sugestao])}` : ''}</small>`}</td>
      ${Object.keys(C.redes).map((r) => `<td>${chipEnvio(x.redes[r].estado, x.redes[r].erro)} <small class="neutro">${esc(x.redes[r].hora)}</small>${x.redes[r].url ? ` <a href="${esc(x.redes[r].url)}" target="_blank" rel="noopener"><small>ver</small></a>` : ''}</td>`).join('')}</tr>`).join('')}</table>
    <p class="sub">Uso dos pilares (4 semanas + mês): ${Object.entries(C.uso_pilares).map(([k, n]) => `${esc(C.pilares[k])} ${n}`).join(' · ')}. Os dias vazios recebem o pilar menos usado; o piloto pede o roteiro ao Claude com essa sugestão.</p>`;
  } else if (j.aba === 'comentarios') {
    corpo = `<p class="sub" style="margin-top:0">Comentários das redes conectadas. Quem quer comprar vira lead no Comercial; elogios e perguntas do FAQ o piloto responde sozinho (ajuste em Piloto → Ajustes).</p>
    ${d.comentarios.map((k, i) => `<div class="cartao msg"><div class="cab"><b>@${esc(k.autor)}</b> <span class="chip ${CATEGORIA[k.categoria]?.[0] || ''}">${esc(CATEGORIA[k.categoria]?.[1] || k.categoria)}</span> <small class="neutro">${esc(nomeRede(k.rede))} · ${quandoBr(k.data)}</small></div>
      <blockquote>${esc(k.texto)}</blockquote><textarea class="resp-${i}" rows="2" placeholder="Sua resposta">${esc(k.sugestao)}</textarea>
      <div class="acoes-linha"><button class="bt pri" data-fn="responder" data-i="${i}">Responder</button>${k.categoria !== 'lead' ? `<button class="bt" data-fn="marcarCom" data-i="${i}" data-estado="lead">É lead</button>` : ''}<button class="bt" data-fn="marcarCom" data-i="${i}" data-estado="ignorado">Ignorar</button></div></div>`).join('') || '<div class="vazio">Nenhum comentário novo. Eles chegam a cada sincronização.</div>'}
    ${d.aguardando.length ? `<h2>Responder pelo app (${d.aguardando.length})</h2><p class="sub">Esta rede não deixa responder pela API (o TikTok, por exemplo). A resposta está pronta: copie e cole no app.</p>
      <div class="lista">${d.aguardando.map((k, i) => `<div class="linha-item"><div class="cresce"><b>@${esc(k.autor)}</b> <small class="neutro">${esc(nomeRede(k.rede))}</small><small style="white-space:normal">${esc(k.texto)} → ${esc(k.resposta)}</small></div>
        <button class="bt mini" data-fn="copiarResp" data-i="${i}">Copiar</button><button class="bt mini" data-fn="marcarCom" data-lista="aguardando" data-i="${i}" data-estado="respondido">Já respondi</button></div>`).join('')}</div>` : ''}`;
  } else if (j.aba === 'resultados') {
    corpo = `<p class="sub" style="margin-top:0">Cada post, 7 dias depois, contra a mediana dos 10 anteriores da mesma rede. O resultado entra sozinho na biblioteca de ganchos: o roteirista passa a repetir o que funcionou no seu perfil.</p>
    <table class="tab"><tr><th>Data</th><th>Rede</th><th>Post</th><th>Views</th><th>Resultado</th><th>Salv.</th><th>Comp.</th></tr>${d.resultados.map((r) => `<tr><td>${ddmm(r.data)}</td><td>${esc(nomeRede(r.rede))}</td>
      <td>${r.url ? `<a href="${esc(r.url)}" target="_blank" rel="noopener">${esc((r.texto || '').slice(0, 70))}</a>` : esc((r.texto || '').slice(0, 70))}</td><td>${num(r.views || 0)}</td>
      <td>${r.veredito ? `<span class="chip ${VEREDITO[r.veredito][0]}">${esc(VEREDITO[r.veredito][1])} ${String(r.multiplicador).replace('.', ',')}x</span>` : `<small class="neutro">${(Date.now() - new Date(r.data.slice(0, 10))) / 864e5 < 7 ? 'menos de 7 dias' : 'sem base (precisa de 3 posts antes)'}</small>`}</td>
      <td>${r.salvamentos ?? '—'}</td><td>${r.compartilhamentos ?? '—'}</td></tr>`).join('') || '<tr><td colspan="7">Sem posts sincronizados ainda: conecte um provedor e clique em Sincronizar.</td></tr>'}</table>`;
  } else {
    const acoesEnvio = (e) => `${['na_fila', 'aguardando_aprovacao', 'aprovado', 'erro'].includes(e.estado) ? `<button class="bt mini" data-fn="segurar" data-post="${esc(e.post)}" data-rede="${e.rede}" title="Não vai ao ar nesta rede">Segurar</button>` : ''}
      ${e.estado === 'aguardando_aprovacao' ? `<button class="bt mini pri" data-fn="aprovar" data-post="${esc(e.post)}" data-rede="${e.rede}">Aprovar</button>` : ''}
      ${['erro', 'perdido', 'segurado'].includes(e.estado) ? `<button class="bt mini" data-fn="tentar" data-post="${esc(e.post)}" data-rede="${e.rede}">Tentar de novo</button>` : ''}`;
    corpo = `${caidas}<div class="modos">${Object.entries(P.modos).map(([k, r]) => `<button class="modo ${c.modo === k ? 'on' : ''}" data-fn="modo" data-m="${k}"><b>${esc(r)}</b><small>${{ automatico: 'pesquisa, produz e publica sozinho; você pode segurar qualquer post', aprovar: 'prepara tudo e espera o seu ok em cada post', pausado: 'não produz nem publica; números e comentários continuam' }[k]}</small></button>`).join('')}</div>
    ${semRede ? '<div class="faixa">Nenhuma rede tem por onde publicar. <button class="bt mini pri" data-abrir="conexoes">Abrir Conexões</button></div>' : ''}
    ${P.ia ? '' : '<div class="faixa">Claude Code não encontrado: o piloto produz e publica, mas não escreve roteiros novos sozinho.</div>'}
    <div class="acoes"><button class="bt pri" data-acao="piloto">${icone('play')} Rodar agora</button><button class="bt" data-fn="ajustes">Ajustes</button><button class="bt" data-abrir="conexoes">Conexões</button></div>
    <h2>Fila de publicação (${P.fila.length})</h2><table class="tab"><tr><th>Quando</th><th>Rede</th><th>Post</th><th>Situação</th><th></th></tr>${P.fila.map((e) => `<tr><td>${quandoBr(e.quando)}</td><td>${esc(nomeRede(e.rede))}</td>
      <td>${esc(e.post.slice(11).replace(/-/g, ' '))}${e.erro ? `<br><small class="${e.estado === 'erro' ? 'ruim' : 'neutro'}">${esc(e.erro)}</small>` : ''}</td><td>${chipEnvio(e.estado)}${e.url ? ` <a href="${esc(e.url)}" target="_blank" rel="noopener"><small>ver</small></a>` : ''}</td>
      <td class="acoes-linha">${acoesEnvio(e)}</td></tr>`).join('') || '<tr><td colspan="5">Nada na fila. O piloto coloca aqui cada post pronto, em cada rede ligada.</td></tr>'}</table>
    <h2>O que o piloto fez</h2><div class="lista">${P.diario.slice(0, 25).map((x) => `<div class="linha-item ${x.ok ? '' : 'achado alto'}"><small class="neutro" style="min-width:110px">${quandoBr(x.quando)}</small><div class="cresce"><small style="white-space:normal;color:var(--tinta)"><b>${esc(x.evento)}</b> · ${esc(x.detalhe)}</small></div></div>`).join('') || '<p class="sub">Ainda não rodou. Clique em Rodar agora ou rode o agendar.cmd para ele rodar de hora em hora.</p>'}</div>`;
  }
  const novos = d.comentarios.length;
  j.corpo.innerHTML = `<div class="pagina"><h1>Rede social</h1><p class="sub">Piloto ${esc(P.modos[c.modo])} · ${Object.entries(d.redes).filter(([, r]) => r.ativa && r.via).map(([r]) => nomeRede(r)).join(', ') || 'nenhuma rede ligada'}</p>
  ${abas(j, [['piloto', 'Piloto', P.fila.filter((e) => ['aguardando_aprovacao', 'erro'].includes(e.estado)).length || ''], ['calendario', 'Calendário do mês'], ['comentarios', 'Comentários', novos || ''], ['resultados', 'Resultados']])}${corpo}</div>`;
}

// ------------------------------------------------------------------ apps: tendências e concorrentes
// linhas da "Pauta sugerida" do radar (| # | Nota | Pilar | Assunto | Ângulo |) viram itens com botão
function pautaDoRadar(texto) {
  return String(texto || '').split('\n').filter((l) => /^\|\s*\d+\s*\|/.test(l)).map((l) => l.replace(/^\||\|$/g, '').split('|').map((c) => c.trim()))
    .filter((c) => c.length >= 5).map(([n, nota, pilar, assunto, angulo]) => ({ n, nota, pilar, assunto: assunto.replace(/\*\*|`/g, ''), angulo: angulo.replace(/^"|"$/g, '').replace(/`/g, '') }));
}
async function renderRelatorio(j, qual) {
  const d = await api(`/api/app/${qual}`);
  const acao = qual === 'tendencias' ? ['radar', 'Rodar o radar agora'] : ['vigia', 'Checar concorrentes agora'];
  const titulo = qual === 'tendencias' ? 'Tendências do nicho' : 'Concorrentes';
  const sub = qual === 'tendencias' ? 'Assuntos em alta nos 5 pilares, com nota de 0 a 100.' : `Vigiando ${esc((d.concorrentes || []).join(', '))}.`;
  const pauta = qual === 'tendencias' && d.relatorio ? pautaDoRadar(d.relatorio.texto) : [];
  j.fns = {
    roteiro: ({ i }) => { const x = pauta[+i]; pedirEquipe(`Use o roteirista: roteiro de reel sobre "${x.assunto}" (pilar ${x.pilar}), com o ângulo "${x.angulo}". Antes, confirme os fatos numa fonte oficial (passo 3 do AGENTE.md); se não der para confirmar, me avise e sugira outro tema da pauta. Siga o formato dos roteiros (gancho de até 9 palavras, 2 a 4 itens, CTA "Salva pra testar depois"), salve em roteiros/ com a data do próximo horário livre e me mostre para aprovar.`, `Roteiro · ${x.assunto.slice(0, 24)}`); },
    semana: () => pedirEquipe(`Crie os 3 reels da semana a partir da pauta do radar mais recente (${d.relatorio.arquivo}), seguindo a rotina /semana. Me mostre os 3 temas e os roteiros para aprovar antes de produzir, e peça confirmação antes de agendar.`, 'Semana de conteúdo'),
    comClaude: () => pedirEquipe(qual === 'tendencias' ? 'Use o pesquisador-mercado: monte o radar de tendências desta semana com busca web, no mesmo formato de radar/2026-10-19.md (pauta sugerida com nota, pilar, assunto e ângulo para pequeno negócio, e fontes). Marque com ⚠️ o que precisa confirmar.' : 'Use o pesquisador-mercado: confira preço, planos e oferta dos concorrentes de comercial/concorrentes.json com busca web e me diga o que mudou e o que isso significa para o preço do CIELLO CRM.', qual === 'tendencias' ? 'Radar' : 'Concorrentes'),
  };
  j.corpo.innerHTML = `<div class="pagina"><h1>${titulo}</h1><p class="sub">${sub}${d.relatorio ? ` · <code>${esc(d.relatorio.arquivo)}</code>` : ''}</p>
  <div class="acoes" style="margin-top:0"><button class="bt pri" data-acao="${acao[0]}">${icone('play')} ${acao[1]}</button><button class="bt" data-fn="comClaude" title="Sem internet no radar? O Claude monta com busca web">Montar com o Claude</button><button class="bt" data-abrir="agente:pesquisador-mercado">Pesquisador</button></div>
  ${pauta.length ? `<h2>Pauta sugerida</h2><div class="lista">${pauta.map((x, i) => `<div class="linha-item"><span class="chip ${+x.nota >= 75 ? 'pronto' : ''}">${esc(x.nota)}</span><div class="cresce"><b>${esc(x.assunto)}</b><small style="white-space:normal">${esc(x.pilar)} · ${esc(x.angulo)}</small></div><button class="bt mini pri" data-fn="roteiro" data-i="${i}">Virar roteiro</button></div>`).join('')}</div>
    <div class="acoes"><button class="bt" data-fn="semana">${icone('play')} Fazer os 3 reels da semana com esta pauta</button></div><h2>Relatório completo</h2>` : ''}
  ${d.relatorio ? `<div class="cartao md" style="margin-top:12px">${md(d.relatorio.texto)}</div>` : '<div class="vazio" style="margin-top:12px">Nenhum relatório ainda.</div>'}</div>`;
}

// ------------------------------------------------------------------ apps: anúncios
async function renderAnuncios(j) {
  const d = await api('/api/app/anuncios'); const r = d.resumo;
  const kpi = (t, v) => `<div class="kpi"><small>${t}</small><strong>${v}</strong></div>`;
  const porNome = Object.fromEntries((d.campanhas || []).map((c) => [c.nome, c]));
  const campos = (c = {}) => [{ nome: 'nome', rotulo: 'Nome da campanha', valor: c.nome, obrigatorio: true }, { nome: 'inicio', rotulo: 'Início', tipo: 'data', valor: c.inicio || hojeISO(), meia: true }, { nome: 'fim', rotulo: 'Fim', tipo: 'data', valor: c.fim, meia: true },
    { nome: 'objetivo', rotulo: 'Objetivo', valor: c.objetivo, exemplo: 'mensagens no WhatsApp', meia: true }, { nome: 'publico', rotulo: 'Público', valor: c.publico, meia: true }, { nome: 'criativo', rotulo: 'Criativo', valor: c.criativo },
    ...[['gasto', 'Gasto (R$)'], ['impressoes', 'Impressões'], ['cliques', 'Cliques'], ['conversas', 'Conversas'], ['demos', 'Demos'], ['clientes', 'Clientes']].map(([k, r]) => ({ nome: k, rotulo: r, tipo: 'numero', valor: c[k] != null ? String(c[k]).replace('.', ',') : '', meia: true }))];
  j.fns = {
    nova: () => dialogo(j, { titulo: 'Registrar campanha', texto: 'Copie os números do Gerenciador de Anúncios. Só número real, nada estimado.', campos: campos(), enviar: (x) => operar('anuncio', x) }),
    editar: ({ nome: n }) => dialogo(j, { titulo: `Atualizar ${n}`, campos: campos(porNome[n]), enviar: (x) => operar('anuncio', x) }),
  };
  j.corpo.innerHTML = `<div class="pagina"><h1>Anúncios</h1><p class="sub">Testes no Meta Ads, lidos do Gerenciador de Anúncios ou do Metricool.</p>
  <div class="acoes topo"><button class="bt pri" data-fn="nova">+ Campanha</button></div>
  ${r ? `<div class="kpis">${kpi('Investido', brl(r.gasto))}${kpi('Conversas', num(r.conversas))}${kpi('Custo por conversa', r.custo_conversa != null ? brl(r.custo_conversa) : '—')}${kpi('Custo por cliente', r.custo_cliente != null ? brl(r.custo_cliente) : '—')}</div>
  <h2>Campanhas</h2><table class="tab"><tr><th>Campanha</th><th>Período</th><th>Gasto</th><th>Conversas</th><th>Demos</th><th>Clientes</th><th></th></tr>${d.campanhas.map((c) => `<tr><td><b>${esc(c.nome)}</b><br><small class="neutro">${esc(c.publico || '')}</small></td><td>${ddmm(c.inicio)}–${ddmm(c.fim)}</td><td>${brl(c.gasto)}</td><td>${num(c.conversas)}</td><td>${num(c.demos)}</td><td>${num(c.clientes)}</td><td><button class="bt mini" data-fn="editar" data-nome="${esc(c.nome)}">Atualizar</button></td></tr>`).join('')}</table>`
    : '<div class="vazio">Nenhuma campanha registrada ainda. Clique em <b>+ Campanha</b> e copie os números do Gerenciador de Anúncios.</div>'}
  <div class="acoes"><button class="bt pri" data-abrir="agente:gestor-anuncios">Gestor de anúncios</button></div></div>`;
}

// ------------------------------------------------------------------ apps: estúdio de vídeo (central/estudio_video.py, HyperFrames)
async function renderVideo(j) {
  const d = await api('/api/app/video');
  j.modelo = j.modelo || 'escuro';
  j.gerando = j.gerando || {};
  const m = d.modelos;
  j.fns = {
    modelo: ({ m: k }) => { j.modelo = k; desenhar(j, true); },
    novo: () => dialogo(j, { titulo: 'Novo roteiro', texto: 'Escreva como você falaria. Cada linha vira uma cena com título e legenda. Sem o Claude: o vídeo sai com a voz escolhida no Estúdio de Voz.',
      campos: [{ nome: 'data', rotulo: 'Data do post', tipo: 'escolha', opcoes: d.proximos.map((x) => [x, `${ddmm(x)} (próximo horário livre)`]), meia: true },
        { nome: 'pilar', rotulo: 'Pilar', tipo: 'escolha', opcoes: [['comandos', 'Comandos'], ['lancamentos', 'Lançamentos'], ['repositorios', 'Repositórios'], ['economizar', 'Economizar'], ['negocio', 'Negócio / CRM']], meia: true },
        { nome: 'gancho', rotulo: 'Gancho (a 1ª frase, até 9 palavras)', obrigatorio: true, exemplo: 'Três comandos do ChatGPT que respondem cliente por você' },
        { nome: 'itens', rotulo: 'Itens (um por linha, 2 a 4)', tipo: 'area', obrigatorio: true, exemplo: 'Primeiro: responda como atendente da minha loja…\nSegundo: transforme a conversa em orçamento…' },
        { nome: 'cta', rotulo: 'Chamada final', valor: 'Salva pra testar depois e me chama no direct.' }],
      botao: 'Criar roteiro', enviar: async (x) => { const r = await operar('video_roteiro', x); if (r.ok) desenhar(j, true); return r; } }),
    gerar: async ({ post, rascunho }) => {
      silenciar('produtor-video', true);
      const r = await operar('video_gerar', { post, modelo: j.modelo, rascunho: rascunho === '1' });
      if (!r.ok) { silenciar('produtor-video', false); return aviso({ titulo: 'Não deu', texto: r.saida, cor: '#C8442F' }); }
      j.gerando[post] = { linha: 'começando…' }; desenhar(j, true);
      const timer = setInterval(async () => {
        let ex; try { ex = await api(`/api/execucao/${encodeURIComponent(r.execucao)}`); } catch { return; }
        const linhas = (ex.saida || '').trim().split('\n').filter((l) => !/^\s|^\[(init|Browser|INFO|HyperFrames)/.test(l));
        j.gerando[post] = { linha: linhas.slice(-1)[0] || 'trabalhando…' };
        if (ex.terminou) {
          clearInterval(timer); delete j.gerando[post]; silenciar('produtor-video', false);
          aviso(ex.codigo === 0 ? { titulo: 'Vídeo pronto', texto: 'Confira a prévia e clique em Usar como vídeo final.', cor: '#1F8A4C' } : { titulo: 'O vídeo não saiu', texto: linhas.slice(-1)[0] || '', cor: '#C8442F' });
        }
        const lin = $(`[data-progresso="${post}"]`, j.corpo); if (lin && !ex.terminou) lin.textContent = j.gerando[post].linha; else desenhar(j, true);
      }, 1500);
    },
    usar: async ({ post }) => { const r = await rapido('video_usar', { post, modelo: j.modelo }, 'Vídeo final atualizado'); if (r.ok) desenhar(j, true); },
  };
  const cartao = (p) => {
    const tem = p.rascunhos[j.modelo]; const g = j.gerando[p.post];
    const chip = (ok, r) => `<span class="etapa-post ${ok ? 'feita' : ''}">${ok ? '✓ ' : ''}${r}</span>`;
    return `<div class="cartao post-video"><div class="post-cab"><b>${ddmm(p.data)}</b> <span>${esc(p.titulo)}</span></div>
      <div class="etapas-post">${chip(p.etapas.roteiro, 'Roteiro')}<i>›</i>${chip(p.narracao, 'Narração')}<i>›</i>${chip(tem, `Rascunho ${esc(m[j.modelo].nome.split(' ')[1])}`)}<i>›</i>${chip(p.etapas.final, 'Vídeo final')}</div>
      ${tem ? `<video class="previa" controls preload="metadata" src="/midia/estudio/${encodeURIComponent(p.post)}-${j.modelo}.mp4?v=${Date.now()}"></video>` : ''}
      <div class="acoes-linha">${g ? `<span class="girando"></span><small class="neutro" data-progresso="${esc(p.post)}">${esc(g.linha)}</small>`
        : `<button class="bt pri" data-fn="gerar" data-post="${esc(p.post)}" ${d.hyperframes ? '' : 'disabled'}>${icone('play')} ${tem ? 'Gerar de novo' : 'Gerar vídeo'}</button>
           <button class="bt" data-fn="gerar" data-post="${esc(p.post)}" data-rascunho="1" ${d.hyperframes ? '' : 'disabled'} title="Qualidade menor, sai mais rápido">Rascunho rápido</button>
           ${tem ? `<button class="bt" data-fn="usar" data-post="${esc(p.post)}" title="Copia para midia/final/ (o que vai para o Instagram)">Usar como vídeo final</button>` : ''}`}</div></div>`;
  };
  j.corpo.innerHTML = `<div class="pagina"><h1>Estúdio de Vídeo</h1><p class="sub">Roteiro → narração com a voz do Estúdio de Voz (agora: <b>${esc(d.voz)}</b>) → vídeo com a marca da Ciello, legenda e trilha. Feito no seu PC com o HyperFrames.</p>${SEM_CLAUDE}
    ${d.hyperframes ? '' : '<div class="faixa">O motor de vídeo (HyperFrames) ainda não está instalado. Rode o <b>instalar.cmd</b> de novo: ele instala em reels/.</div>'}
    <div class="acoes topo"><button class="bt pri" data-fn="novo">+ Novo roteiro</button><button class="bt" data-abrir="voz">Estúdio de Voz</button><button class="bt" data-abrir="objetivos" title="Os agentes escrevem os roteiros">Pedir roteiros à equipe</button></div>
    <h2>Modelo</h2><div class="modelos">${Object.entries(m).map(([k, x]) => `<button class="modelo ${j.modelo === k ? 'on' : ''}" data-fn="modelo" data-m="${k}"><span class="amostra" style="background:${x.fundo}"><i style="color:${x.texto}">Título</i><i style="color:${x.ouro}">em destaque</i></span><b>${esc(x.nome)}</b><small>${esc(x.descricao)}</small></button>`).join('')}</div>
    <h2>Roteiros</h2><div class="quadro-posts">${d.posts.map(cartao).join('') || '<div class="vazio">Nenhum roteiro. Clique em <b>+ Novo roteiro</b>.</div>'}</div></div>`;
}

// ------------------------------------------------------------------ apps: atendimento (central/atendimento.py, comercial/faq.md)
async function renderAtendimento(j) {
  const d = await api('/api/app/atendimento');
  j.achados = j.achados || null;
  const faltam = d.faq.filter((x) => !x.completa);
  const cliente = () => d.clientes.find((c) => c.id === ($('[name=cliente]', j.corpo) || {}).value);
  const linkPara = (texto) => { const c = cliente(); return c ? zap(c.whatsapp) + `?text=${encodeURIComponent(texto)}` : ''; };
  const editar = (it, titulo) => dialogo(j, { titulo, texto: it ? `Seção: ${esc(it.secao)}. A resposta fica no FAQ e o Sucesso do Cliente passa a usar.` : 'Pergunta nova para o FAQ: escreva como o cliente pergunta e a resposta como você responderia.',
    campos: [{ nome: 'pergunta', rotulo: 'Pergunta', valor: it ? it.pergunta : ($('.objetivo-texto', j.corpo)?.value || ''), obrigatorio: true },
      { nome: 'resposta', rotulo: 'Resposta', tipo: 'area', valor: it ? it.resposta.replace(/⟨[^⟩]*⟩\.?/g, '').trim() : '', obrigatorio: true }],
    botao: 'Salvar no FAQ', enviar: async (x) => { const r = await operar('faq_salvar', { ...x, i: it ? it.i : '' }); if (r.ok) desenhar(j, true); return r; } });
  j.fns = {
    mandar: async () => {
      const t = $('.objetivo-texto', j.corpo).value.trim(); if (!t) return;
      const r = await operar('faq_buscar', { texto: t }); j.achados = r.achados || []; j.pergunta = t;
      document.activeElement?.blur(); desenhar(j, true); // sem o blur, a atualização espera você sair da caixa de texto
    },
    copiar: ({ i }) => copiar($(`[data-resp="${i}"]`, j.corpo).value),
    zap: ({ i }) => { const l = linkPara($(`[data-resp="${i}"]`, j.corpo).value); if (l) window.open(l, '_blank', 'noopener'); else aviso({ titulo: 'Escolha o cliente', texto: 'Selecione para quem é a resposta (ou copie e cole no WhatsApp).', cor: '#E0A81C' }); },
    completar: ({ i }) => editar(d.faq[+i], 'Completar o FAQ'),
    nova: () => editar(null, 'Pergunta nova'),
    claude: () => pedirEquipe(`Use o sucesso-cliente: um cliente perguntou "${j.pergunta || $('.objetivo-texto', j.corpo).value}". Responda com base em comercial/faq.md, no tom do Mateus (curto, simpático, sem prometer o que não está no FAQ). Se a resposta não estiver no FAQ, escreva um rascunho e me pergunte antes de acrescentar. Não envie nada.`, 'Atendimento'),
  };
  const pergunta = j.pergunta || '';
  j.corpo.innerHTML = `<div class="pagina"><h1>Atendimento</h1><p class="sub">Cole a pergunta do cliente: a resposta sai do FAQ da Ciello, pronta para revisar e mandar no WhatsApp.</p>${SEM_CLAUDE}
  <div class="objetivo compacto"><textarea class="objetivo-texto" rows="2" placeholder="Ex.: funciona no celular? / quanto fica por mês? / esqueci de pagar o boleto">${esc(pergunta)}</textarea><button class="bt pri" data-fn="mandar">Achar resposta</button></div>
  <div class="campos-voz" style="margin:8px 0 0"><label>Para quem é a resposta<select name="cliente"><option value="">escolha o cliente (para o link do WhatsApp)</option>${d.clientes.map((c) => `<option value="${esc(c.id)}">${esc(c.empresa)}${c.contato ? ` · ${esc(c.contato)}` : ''}</option>`).join('')}</select></label></div>
  ${j.achados ? (j.achados.length ? `<h2>Respostas do FAQ</h2>${j.achados.map((a, i) => `<div class="cartao msg"><div class="cab"><b>${esc(a.pergunta)}</b> <small class="neutro">${esc(a.secao)}</small>${a.completa ? '' : ' <span class="chip esperando">resposta incompleta</span>'}</div>
      <textarea class="texto-msg" data-resp="${i}" rows="3">${esc(a.resposta)}</textarea>
      <div class="acoes-linha"><button class="bt wa" data-fn="zap" data-i="${i}">Abrir no WhatsApp</button><button class="bt" data-fn="copiar" data-i="${i}">Copiar</button>${a.completa ? '' : `<button class="bt pri" data-fn="completar" data-i="${a.i}">Completar no FAQ</button>`}</div></div>`).join('')}`
    : '<div class="vazio">Nada no FAQ sobre isso.</div>') + `<div class="acoes"><button class="bt" data-fn="nova">Escrever a resposta e guardar no FAQ</button><button class="bt" data-fn="claude">Pedir ao Sucesso do Cliente (Claude)</button></div>` : ''}
  ${faltam.length ? `<h2>FAQ incompleto (${faltam.length})</h2><p class="sub">São as perguntas que todo cliente faz. Responda uma vez e o atendimento passa a usar.</p><div class="lista">${faltam.map((x) => `<div class="linha-item"><div class="cresce"><b>${esc(x.pergunta)}</b><small>${esc(x.resposta || '(vazia)')}</small></div><button class="bt mini pri" data-fn="completar" data-i="${x.i}">Responder</button></div>`).join('')}</div>` : ''}
  <details class="passados"><summary>FAQ inteiro (${d.faq.length})</summary><div class="lista">${d.faq.map((x) => `<div class="linha-item"><div class="cresce"><b>${esc(x.pergunta)}</b><small style="white-space:normal">${esc(x.resposta)}</small></div><button class="bt mini" data-fn="completar" data-i="${x.i}">Editar</button></div>`).join('')}</div></details></div>`;
}

// ------------------------------------------------------------------ apps: objetivos e esteiras
// Você diz o objetivo; o Claude Code abre aqui dentro como coordenador e distribui o trabalho entre os agentes
// (cada um aparece trabalhando no escritório). Nada sai do PC sem a sua aprovação.
function promptObjetivo(objetivo) {
  return `Objetivo do Mateus: ${objetivo}

Você é o Gerente da Ciello (siga .claude/agents/gerente.md) e coordena a equipe (agentes em .claude/agents). Faça assim:
1. Monte um plano curto: quem faz o quê e em que ordem (o que não depende de outra etapa roda em paralelo). Mostre o plano em poucas linhas e siga.
2. Delegue cada etapa ao agente certo com a ferramenta Task: subagent_type com o nome do agente e a descrição começando pelo nome (ex.: "roteirista: 3 roteiros da semana"), para ele aparecer trabalhando no escritório.
3. Use as ferramentas de central/ e as regras do AGENTE.md e de docs/equipe.md. A narração usa a voz escolhida no Estúdio de Voz (python central/voz.py sem --motor).
4. Publicar ou agendar post segue o modo do piloto (python central/piloto.py estado: Automático publica, Aprovar espera o meu ok). Enviar mensagem ou e-mail, subir anúncio e gastar dinheiro: pare e peça minha aprovação.
5. No fim: um resumo curto do que ficou pronto e onde está cada arquivo.`;
}
function pedirEquipe(objetivo, titulo = 'Objetivo') {
  objetivo = String(objetivo || '').trim(); if (!objetivo) return;
  fecharMenus();
  SALVO.objetivos = [objetivo, ...(SALVO.objetivos || []).filter((o) => o !== objetivo)].slice(0, 6); salvar();
  abrirTerminal({ prompt: promptObjetivo(objetivo), titulo });
}
const ESTEIRAS = [
  { id: 'semana', titulo: 'Semana de conteúdo', desc: 'Pesquisa as novidades, escreve os roteiros, narra, monta os vídeos, faz capa e legenda e agenda no Metricool.',
    agentes: ['pesquisador-mercado', 'roteirista', 'produtor-video', 'produtor-imagem', 'postagem'],
    campos: [['n', 'Vídeos', '3'], ['tema', 'Assunto', 'novidades de IA da semana para pequenos negócios']],
    pedido: (v) => `Crie ${v.n || 3} vídeos sobre ${v.tema || 'as novidades de IA da semana'} para o @ciellotec seguindo a rotina /semana: pesquisa e checagem de fatos, roteiros, narração, vídeo, capa, legenda e agendamento no Metricool nos próximos horários (seg, qua e sex às 10h). Me mostre os temas e os roteiros para eu aprovar antes de produzir, e peça minha confirmação antes de agendar.` },
  { id: 'video', titulo: 'Um vídeo sobre um tema', desc: 'Roteiro para você aprovar, narração, vídeo, capa e legenda. Fica pronto em midia/final/ sem agendar.',
    agentes: ['roteirista', 'produtor-video', 'produtor-imagem'], campos: [['tema', 'Tema', '']],
    pedido: (v) => `Faça 1 reel sobre: ${v.tema || '(me pergunte o tema)'}. Roteiro (me mostre para aprovar), narração, vídeo, capa e legenda. Não agende: deixe o vídeo final em midia/final/ e me diga onde está.` },
  { id: 'comercial', titulo: 'Prospecção do dia', desc: 'Follow-ups, abordagens novas e respostas para os quentes, prontos na janela Comercial. Nada é enviado.',
    agentes: ['sdr', 'closer'], campos: [['n', 'Abordagens novas', '15']],
    pedido: (v) => `Rode /comercial: follow-ups do dia, ${v.n || 15} abordagens novas e respostas para os leads quentes. Deixe as mensagens prontas na janela Comercial do Ciello OS; não envie nada.` },
  { id: 'bomdia', titulo: 'Bom dia', desc: 'Caixa de entrada, financeiro, pós-venda e comercial numa tela com as 3 prioridades do dia.',
    agentes: ['gerente', 'caixa-entrada', 'financeiro', 'sucesso-cliente'], campos: [], pedido: () => 'Rode /bom-dia e me entregue as 3 prioridades do dia.' },
  { id: 'anuncio', titulo: 'Campanha de anúncio', desc: 'Público, 3 criativos (roteiro e imagem), orçamento e o que medir. Nada sobe no Meta sem você.',
    agentes: ['gestor-anuncios', 'roteirista', 'produtor-imagem'], campos: [['objetivo', 'Para quê', 'conversas no WhatsApp de imobiliárias da região'], ['verba', 'Verba (R$)', '100']],
    pedido: (v) => `Planeje uma campanha de Meta Ads para ${v.objetivo || 'gerar conversas no WhatsApp'} com verba de R$ ${v.verba || 100}: público, 3 criativos (roteiro e imagem), orçamento e o que medir. Não suba nada no Meta: me entregue o plano e os criativos para eu aprovar.` },
  { id: 'sexta', titulo: 'Fechamento da semana', desc: 'Placar, resumo financeiro, vigia dos concorrentes e uma decisão para a próxima semana.',
    agentes: ['gerente', 'financeiro', 'pesquisador-mercado', 'analista'], campos: [], pedido: () => 'Rode /sexta e termine com uma decisão para a próxima semana.' },
];
const EXEMPLOS = ['Crie 3 vídeos das novidades da semana, faça as capas, as legendas e programe as postagens',
  'Encontre 20 imobiliárias em Chapecó e prepare a 1ª mensagem', 'Monte um carrossel explicando o CIELLO CRM', 'Como está a empresa esta semana?'];

async function renderObjetivos(j) {
  if (!equipeCache.length) await puxarEquipe();
  j.params = j.params || {};
  const valor = (e, c) => (j.params[`${e.id}.${c[0]}`] ?? c[2]);
  j.fns = {
    mandar: () => { const t = $('.objetivo-texto', j.corpo); if (t.value.trim()) { pedirEquipe(t.value); t.value = ''; } else t.focus(); },
    exemplo: ({ i }) => { const t = $('.objetivo-texto', j.corpo); t.value = EXEMPLOS[+i]; t.focus(); },
    recente: ({ i }) => pedirEquipe(SALVO.objetivos[+i]),
    esteira: ({ id }) => {
      const e = ESTEIRAS.find((x) => x.id === id);
      const v = Object.fromEntries(e.campos.map((c) => [c[0], String(valor(e, c)).trim()]));
      if (id === 'video' && !v.tema) { aviso({ titulo: 'Falta o tema', texto: 'Escreva o tema do vídeo na esteira.', cor: '#C8442F' }); return; }
      pedirEquipe(e.pedido(v), e.titulo);
    },
    param: (d, el) => { j.params[el.name] = el.value; },
  };
  const texto = $('.objetivo-texto', j.corpo)?.value || '';
  const trabalhando = Object.entries(estadoCache.agentes).filter(([, a]) => a.estado === 'trabalhando' || a.estado === 'esperando');
  const elo = (a) => { const s = estadoAgente(a).estado; return `<span class="elo ${s}" title="${esc(nome(a))}: ${esc(ROTULO_ESTADO[s] || s)}">${sprite(a, 22)}<small>${esc(nome(a))}</small></span>`; };
  j.corpo.innerHTML = `<div class="pagina"><h1>O que você quer fazer?</h1><p class="sub">Diga o objetivo com as suas palavras. O coordenador monta o plano, chama os agentes certos (você vê cada um trabalhando no escritório) e pede a sua aprovação antes de publicar, enviar ou gastar.</p>
  <div class="objetivo"><textarea class="objetivo-texto" rows="3" placeholder="Ex.: crie 3 vídeos das novidades da semana, faça a capa, a descrição e programe a postagem">${esc(texto)}</textarea>
    <div class="acoes-linha"><button class="bt pri" data-fn="mandar">${icone('play')} Mandar para a equipe</button>${EXEMPLOS.map((x, i) => `<button class="chip-ex" data-fn="exemplo" data-i="${i}">${esc(x.length > 46 ? x.slice(0, 44) + '…' : x)}</button>`).join('')}</div></div>
  ${(SALVO.objetivos || []).length ? `<h2>Pedidos recentes</h2><div class="lista">${SALVO.objetivos.map((o, i) => `<div class="linha-item"><div class="cresce">${esc(o.length > 140 ? o.slice(0, 138) + '…' : o)}</div><button class="bt mini" data-fn="recente" data-i="${i}">Pedir de novo</button></div>`).join('')}</div>` : ''}
  ${trabalhando.length ? `<h2>Trabalhando agora</h2><div class="lista">${trabalhando.map(([a, x]) => `<div class="linha-item" data-abrir="agente:${esc(a)}" style="cursor:pointer">${sprite(a, 20)}<div class="cresce"><b>${esc(nome(a))}</b><small>${esc(x.tarefa || '')}</small></div>${chipEstado(x.estado)}</div>`).join('')}</div>` : ''}
  <h2>Esteiras prontas</h2><div class="esteiras">${ESTEIRAS.map((e) => `<div class="cartao esteira"><b>${esc(e.titulo)}</b><p class="sub">${esc(e.desc)}</p>
    <div class="cadeia">${e.agentes.map(elo).join('<i>→</i>')}</div>
    ${e.campos.length ? `<div class="campos-esteira">${e.campos.map((c) => `<label>${esc(c[1])}<input name="${e.id}.${c[0]}" value="${esc(valor(e, c))}" data-mudar="param" ${c[0] === 'n' || c[0] === 'verba' ? 'inputmode="numeric"' : ''}></label>`).join('')}</div>` : ''}
    <button class="bt pri" data-fn="esteira" data-id="${e.id}">${icone('play')} Rodar esteira</button></div>`).join('')}</div>
  <p class="sub" style="margin-top:14px">As esteiras usam o Claude Code (abre a janela do terminal aqui dentro). Sem o Claude, o Financeiro, o Comercial, o Conteúdo e o Estúdio de Voz continuam funcionando.</p></div>`;
}

// ------------------------------------------------------------------ apps: estúdio de voz
const TEXTO_GRAVAR = 'Oi! Aqui é o Mateus, da Ciello, de Chapecó. Eu ajudo pequenas empresas a vender mais pelo WhatsApp, com organização, '
  + 'resposta rápida e um pouco de inteligência artificial. Hoje eu vou te mostrar como isso funciona na prática, passo a passo. Bora?';
const MOTOR_ROTULO = { kokoro: 'Voz pronta (Kokoro)', chatterbox: 'Sua voz (Chatterbox)', voicestudio: 'VoiceStudio', teste: 'Teste' };
// tarefa que você mesmo começou numa janela: o agente não abre outra janela nem repete o aviso de "terminou"
function silenciar(agente, ligado) { suprimir[agente] = ligado ? Infinity : Date.now(); }
async function acompanhar(id, aoTerminar) {
  for (let i = 0; i < 1800; i++) {
    await new Promise((r) => setTimeout(r, 1000));
    let ex; try { ex = await api(`/api/execucao/${encodeURIComponent(id)}`); } catch { continue; }
    if (ex.terminou) return aoTerminar(ex);
  }
  return null;
}
async function renderVoz(j) {
  const d = await api('/api/app/voz'); const p = d.preferencia; const m = d.motores;
  j.teste = j.teste || { motor: p.motor === 'teste' ? 'kokoro' : p.motor, voz: p.voz, perfil: p.perfil, texto: d.texto_padrao };
  const t = j.teste;
  const audio = (arq) => `<audio controls preload="none" src="/api/voz/arquivo/${encodeURIComponent(arq)}?t=${Date.now()}"></audio>`;
  const escolhida = { kokoro: `voz pronta ${(d.vozes_kokoro.find((v) => v[0] === p.voz) || [p.voz, p.voz])[1]}`, chatterbox: 'a sua voz (Chatterbox)', voicestudio: `VoiceStudio${p.perfil ? ` · voz ${p.perfil}` : ''}` }[p.motor] || p.motor;
  j.fns = {
    gravar: async (_, el) => {
      if (j.gravador) { j.gravador.stop(); return; }
      let fluxo; try { fluxo = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: true } }); }
      catch { aviso({ titulo: 'Microfone bloqueado', texto: 'Permita o microfone para o Ciello OS (ícone de cadeado na barra do navegador).', cor: '#C8442F' }); return; }
      const partes = []; const g = new MediaRecorder(fluxo); j.gravador = g; const inicio = Date.now();
      g.ondataavailable = (e) => partes.push(e.data);
      el.innerHTML = '■ Parar'; el.classList.add('gravando');
      const relogioGravacao = setInterval(() => { $('.tempo-gravacao', j.corpo).textContent = `${Math.round((Date.now() - inicio) / 1000)} s`; }, 250);
      g.onstop = async () => {
        clearInterval(relogioGravacao); fluxo.getTracks().forEach((x) => x.stop()); j.gravador = null;
        const blob = new Blob(partes, { type: g.mimeType || 'audio/webm' });
        const ext = (g.mimeType || '').includes('ogg') ? 'ogg' : 'webm';
        const r = await enviarArquivo('voz', new File([blob], `gravacao.${ext}`));
        aviso({ titulo: r.ok ? 'Voz gravada' : 'Não salvou', texto: r.saida, cor: r.ok ? '#1F8A4C' : '#C8442F' });
        desenhar(j, true);
      };
      g.start();
    },
    enviar: async (_, el) => { const f = el.files[0]; if (!f) return; const r = await enviarArquivo('voz', f); aviso({ titulo: r.ok ? 'Voz salva' : 'Não salvou', texto: r.saida, cor: r.ok ? '#1F8A4C' : '#C8442F' }); desenhar(j, true); },
    campo: (_, el) => { t[el.name] = el.value; if (el.name === 'motor') { el.blur(); desenhar(j, true); } },
    ouvir: async () => {
      t.texto = $('[name=texto]', j.corpo).value;
      silenciar('produtor-video', true);
      const r = await operar('voz_testar', t);
      if (!r.ok) return aviso({ titulo: 'Não deu', texto: r.saida, cor: '#C8442F' });
      j.gerando = true; desenhar(j, true);
      acompanhar(r.execucao, (ex) => {
        j.gerando = false; silenciar('produtor-video', false);
        if (ex.codigo !== 0) aviso({ titulo: 'A voz não saiu', texto: ex.saida.trim().split('\n').slice(-2).join(' '), cor: '#C8442F' });
        j.ultimo = ex.codigo === 0 ? r.arquivo : null; desenhar(j, true);
      });
    },
    usar: async () => { const r = await operar('voz_preferir', t); aviso({ titulo: r.ok ? 'Voz dos vídeos escolhida' : 'Não deu', texto: r.saida, cor: r.ok ? '#1F8A4C' : '#C8442F' }); desenhar(j, true); },
    clonarVS: async () => {
      const r = await operar('voz_clonar_vs', {}); j.clonando = true; desenhar(j, true);
      acompanhar(r.execucao, (ex) => { j.clonando = false; aviso({ titulo: ex.codigo === 0 ? 'Voz clonada no VoiceStudio' : 'Não clonou', texto: ex.saida.trim().split('\n').slice(-1)[0], cor: ex.codigo === 0 ? '#1F8A4C' : '#C8442F' }); j.teste = null; desenhar(j, true); });
    },
    vozesVS: async () => { const r = await operar('voz_vozes_vs', {}); if (!r.ok) return aviso({ titulo: 'VoiceStudio', texto: r.saida, cor: '#C8442F' }); j.vozesVS = r.vozes; desenhar(j, true); },
  };
  const falta = !m.kokoro || !m.chatterbox;
  j.corpo.innerHTML = `<div class="pagina"><h1>Estúdio de Voz</h1><p class="sub">Grave a sua voz, ouça como ela fica e escolha a voz dos vídeos. Hoje os vídeos saem com <b>${esc(escolhida)}</b>.</p>${SEM_CLAUDE}
  ${falta ? `<div class="faixa">${!m.kokoro && !m.chatterbox ? 'A voz ainda não está instalada neste PC.' : `Falta instalar ${!m.kokoro ? 'o Kokoro' : 'o Chatterbox'}.`} Baixa uns 3 GB e precisa do Python 3.12. <button class="bt pri mini" data-acao="voz_instalar">Instalar agora</button></div>` : ''}
  <h2>1. Sua voz</h2><div class="cartao">
    ${d.amostra.existe ? `<p><b>Gravação salva</b> · ${d.amostra.duracao ?? '?'} s · ${esc(d.amostra.quando)}</p>${audio('amostra.wav')}` : '<p>Ainda não tem gravação. Leia o texto abaixo em voz alta, num lugar silencioso, no seu ritmo normal (de 10 a 20 segundos).</p>'}
    <blockquote class="ler">${esc(TEXTO_GRAVAR)}</blockquote>
    <div class="acoes-linha"><button class="bt pri" data-fn="gravar">● ${d.amostra.existe ? 'Gravar de novo' : 'Gravar'}</button><span class="tempo-gravacao neutro"></span>
      <label class="bt">Enviar um áudio<input type="file" accept="audio/*" data-mudar="enviar" hidden></label></div>
    <small class="neutro">A gravação fica só no seu PC (marca/voz-mateus.wav, fora do GitHub).</small></div>
  <h2>2. Testar</h2><div class="cartao">
    <div class="campos-voz"><label>Motor<select name="motor" data-mudar="campo">${['kokoro', 'chatterbox', 'voicestudio'].map((k) => `<option value="${k}" ${t.motor === k ? 'selected' : ''}>${MOTOR_ROTULO[k]}${k !== 'kokoro' && !m[k] ? ' (indisponível)' : ''}</option>`).join('')}</select></label>
      ${t.motor === 'kokoro' ? `<label>Voz<select name="voz" data-mudar="campo">${d.vozes_kokoro.map(([v, r]) => `<option value="${v}" ${t.voz === v ? 'selected' : ''}>${esc(r)}</option>`).join('')}</select></label>` : ''}
      ${t.motor === 'voicestudio' ? `<label>Voz no VoiceStudio${j.vozesVS ? `<select name="perfil" data-mudar="campo"><option value="">a padrão do app</option>${j.vozesVS.map((v) => `<option value="${esc(v.id)}" ${t.perfil === v.id ? 'selected' : ''}>${esc(v.nome || v.id)}</option>`).join('')}</select>` : `<button class="bt mini" data-fn="vozesVS" ${m.voicestudio ? '' : 'disabled'}>Carregar vozes</button>`}</label>` : ''}</div>
    ${t.motor === 'chatterbox' && !d.amostra.existe ? '<p class="ruim">O Chatterbox clona a partir da sua gravação: grave primeiro (passo 1).</p>' : ''}
    ${t.motor === 'chatterbox' ? '<p class="sub">No processador, a 1ª vez baixa o modelo (uns minutos) e cada frase leva de 20 s a 1 min.</p>' : ''}
    <textarea name="texto" rows="2">${esc(t.texto)}</textarea>
    <div class="acoes-linha"><button class="bt pri" data-fn="ouvir" ${j.gerando ? 'disabled' : ''}>${j.gerando ? '<span class="girando"></span> Gerando…' : `${icone('play')} Ouvir`}</button>
      ${j.ultimo ? audio(j.ultimo) : ''}<button class="bt" data-fn="usar" title="Todos os vídeos novos saem com esta voz">Usar esta voz nos vídeos</button></div>
    ${d.testes.length ? `<h3>Testes anteriores</h3><div class="lista">${d.testes.map((x) => `<div class="linha-item"><div class="cresce"><b>${esc(MOTOR_ROTULO[x.motor] || x.motor)}</b><small>${esc(x.quando)} · ${x.duracao ?? '?'} s</small></div>${audio(x.arquivo)}</div>`).join('')}</div>` : ''}</div>
  <h2>VoiceStudio</h2><div class="cartao">
    <p><span class="chip ${m.voicestudio ? 'pronto' : 'parado'}"><i></i>${m.voicestudio ? 'aberto neste PC' : 'fechado ou não instalado'}</span></p>
    <p class="sub">Alternativa local ao ElevenLabs (clonagem, mais de 600 idiomas). Roda como programa separado (licença AGPL-3.0): o Ciello só usa o áudio que ele gera, pela API local dele.</p>
    ${m.voicestudio ? `<div class="acoes-linha"><button class="bt pri" data-fn="clonarVS" ${d.amostra.existe && !j.clonando ? '' : 'disabled'}>${j.clonando ? '<span class="girando"></span> Clonando…' : 'Clonar a minha gravação no VoiceStudio'}</button><small class="neutro">Na 1ª vez ele baixa o modelo (uns 2 GB).</small></div>`
      : `<ol class="passos-vs"><li>Baixe o instalador para Windows em <a href="https://github.com/debpalash/VoiceStudio/releases" target="_blank" rel="noopener">github.com/debpalash/VoiceStudio/releases</a> e instale.</li><li>Abra o VoiceStudio e deixe aberto.</li><li>Volte aqui: este cartão fica verde e libera a clonagem.</li></ol>`}</div></div>`;
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
  const painel = $('.iniciar-agente', j.corpo) || painelIniciar(a.nome); // o que você está digitando não se perde
  const foco = document.activeElement && painel.contains(document.activeElement) ? document.activeElement : null;
  j.corpo.innerHTML = `<div class="cab-agente"><div class="avatar">${sprite(a.nome, 44)}</div><div><h1>${esc(nome(a.nome))}</h1><p>${esc(papel(a.descricao))}</p><div style="margin-top:8px">${chipEstado(s.estado)} ${s.tarefa && s.estado !== 'parado' ? `<small class="neutro">${esc(s.tarefa)}</small>` : ''}${tarefaNoEscritorio(a.nome) ? `<small class="neutro" style="display:block;margin-top:4px">pedido no escritório: ${esc(tarefaNoEscritorio(a.nome))}</small>` : ''}</div></div></div>
  <div class="pagina"><div class="lugar-iniciar"></div><h2>O que faz</h2><p>${esc(resto.join(': ').replace(/ Use proactively.*$/, '') || a.descricao)}</p>
  ${a.acoes.length ? `<h2>Rodar agora</h2><div class="acoes" style="margin-top:0">${a.acoes.map((x, i) => `<button class="bt ${i ? '' : 'pri'}" data-acao="${esc(x.id)}">${icone('play')} ${esc(x.rotulo)}</button>`).join('')}</div>` : ''}
  ${COMANDOS[a.nome] ? `<h2>No Claude Code</h2><p class="comandos">${COMANDOS[a.nome].map((c) => `<code>${c}</code>`).join('')} ou "use o ${esc(a.nome)} para…"</p>` : ''}
  <h2>Últimas atividades</h2><div class="lista">${eventos.map((e) => `<div class="linha-item"><small style="width:46px">${esc(e.ts.slice(11, 16))}</small><div class="cresce">${esc(e.tarefa || '—')}</div>${chipEstado(e.estado)}</div>`).join('') || '<p class="sub">Ainda não trabalhou nesta sessão.</p>'}</div></div>`;
  $('.lugar-iniciar', j.corpo).replaceWith(painel);
  if (foco) foco.focus();
}

// Iniciar: o agente começa pelo terminal do Claude aqui dentro; no escritório ele vai para um PC e trabalha
const SUGESTOES = {
  sdr: ['gerar 20 leads de odontologia em Chapecó e escrever a 1ª mensagem', 'listar os follow-ups de hoje'],
  closer: ['preparar a proposta para o lead que pediu preço', 'responder a objeção "está caro"'],
  'pesquisador-mercado': ['pesquisar o que está em alta em IA para vendas esta semana', 'analisar os 3 concorrentes principais'],
  roteirista: ['transformar a pauta da semana em 3 roteiros de reel'], 'produtor-video': ['produzir o vídeo do roteiro aprovado'],
  'produtor-imagem': ['fazer as capas dos reels da semana'], postagem: ['agendar os posts prontos no Metricool'],
  analista: ['montar o retrato semanal do Instagram'], 'gestor-anuncios': ['planejar uma campanha de R$ 300 para o CRM'],
  gerente: ['montar o resumo do dia com as 3 prioridades'], financeiro: ['ver quem está atrasado e preparar as cobranças'],
  'caixa-entrada': ['fazer a triagem do e-mail e sugerir horários de demo'], 'sucesso-cliente': ['responder as dúvidas de clientes de hoje'],
};
function painelIniciar(agente) {
  const el = document.createElement('div');
  el.className = 'iniciar-agente';
  el.innerHTML = `<h2 style="margin-top:0">Iniciar</h2>
    <textarea rows="2" placeholder="O que ${esc(nome(agente))} deve fazer? Ex.: ${esc((SUGESTOES[agente] || ['...'])[0])}"></textarea>
    <div class="sugestoes">${(SUGESTOES[agente] || []).map((t) => `<button class="sugestao" type="button">${esc(t)}</button>`).join('')}</div>
    <div class="acoes" style="margin-top:8px"><button class="bt ouro" data-iniciar>${icone('play')} Iniciar no Claude Code</button>
    ${(COMANDOS[agente] || []).map((c) => `<button class="bt" data-comando="${esc(c)}" title="Roda o comando ${esc(c)}, que chama este agente junto com a equipe">${esc(c)}</button>`).join('')}</div>
    <small class="neutro">Abre o terminal do Claude aqui no OS. No escritório, ${esc(nome(agente))} vai para um PC e começa a trabalhar.</small>`;
  const caixa = $('textarea', el);
  el.addEventListener('click', (e) => {
    const sug = e.target.closest('.sugestao');
    if (sug) { caixa.value = sug.textContent; caixa.focus(); return; }
    const cmd = e.target.closest('[data-comando]');
    if (cmd) return void abrirTerminal({ prompt: cmd.dataset.comando, titulo: cmd.dataset.comando });
    if (e.target.closest('[data-iniciar]')) {
      const tarefa = caixa.value.trim();
      if (!tarefa) { caixa.focus(); caixa.classList.add('falta'); setTimeout(() => caixa.classList.remove('falta'), 900); return; }
      abrirTerminal({ prompt: `Use o subagente ${agente} para: ${tarefa}`, titulo: nome(agente) });
      caixa.value = '';
    }
  });
  caixa.addEventListener('keydown', (e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) $('[data-iniciar]', el).click(); });
  return el;
}

// ------------------------------------------------------------------ terminal do Claude Code dentro do OS (xterm.js)
// abrirTerminal({ prompt, titulo }): abre uma janela com o Claude Code rodando na pasta do assistente; com prompt, ele
// já começa por aquele pedido (ex.: "Use o subagente sdr para: ..."). Cada janela é um processo; fechar encerra.
async function abrirTerminal({ prompt = '', titulo = '' } = {}) {
  let r; try { r = await api('/api/terminal', { prompt, titulo }); } catch { return null; }
  if (!r || !r.id) { aviso({ titulo: 'Terminal', texto: (r && r.erro) || 'Não deu para abrir o terminal.', cor: '#C8442F' }); return null; }
  SALVO.terminais = { ...(SALVO.terminais || {}), [r.id]: titulo };
  return abrir(`term:${r.id}`);
}
function renderTerminal(j) {
  const id = j.chave.slice(5);
  j.corpo.innerHTML = '<div class="terminal-claude"></div>';
  const caixa = $('.terminal-claude', j.corpo);
  if (typeof Terminal === 'undefined') { caixa.textContent = 'xterm.js não carregou (web/vendor/xterm).'; return; }
  const term = new Terminal({ fontFamily: '"Cascadia Mono", Consolas, "Courier New", monospace', fontSize: 13, cursorBlink: true, scrollback: 5000,
    theme: { background: '#13213A', foreground: '#F8F4E8', cursor: '#E0A81C', cursorAccent: '#13213A', selectionBackground: 'rgba(224,168,28,.35)' } });
  const ajuste = new FitAddon.FitAddon(); term.loadAddon(ajuste); term.open(caixa);
  const ws = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/terminal?token=${encodeURIComponent(TOKEN)}&id=${encodeURIComponent(id)}`);
  const mandar = (m) => { if (ws.readyState === 1) ws.send(JSON.stringify(m)); };
  const tamanho = () => { if (!j.el.isConnected || j.min) return; try { ajuste.fit(); } catch { return; } mandar({ tipo: 'tamanho', linhas: term.rows, colunas: term.cols }); };
  let terminou = false;
  ws.onopen = () => { tamanho(); term.focus(); };
  ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.tipo === 'saida') term.write(m.dados); else if (m.tipo === 'fim') { terminou = true; term.write('\r\n\x1b[33m[o Claude Code terminou: feche esta janela ou abra outro terminal na barra de tarefas]\x1b[0m\r\n'); } };
  ws.onclose = () => { if (!terminou) term.write('\r\n\x1b[31m[terminal desconectado: este terminal não existe mais; abra outro na barra de tarefas]\x1b[0m\r\n'); };
  term.onData((d) => mandar({ tipo: 'entrada', dados: d }));
  // Ctrl+C copia quando há seleção (senão vai para o Claude, que interrompe); Ctrl+V cola
  term.attachCustomKeyEventHandler((e) => {
    if (e.type !== 'keydown' || !(e.ctrlKey || e.metaKey)) return true;
    if (e.key.toLowerCase() === 'c' && term.hasSelection()) { navigator.clipboard?.writeText(term.getSelection()); term.clearSelection(); return false; }
    if (e.key.toLowerCase() === 'v') return false; // deixa o navegador colar (o xterm recebe pelo evento de colar)
    return true;
  });
  let espera; const obs = new ResizeObserver(() => { clearTimeout(espera); espera = setTimeout(tamanho, 60); }); obs.observe(caixa);
  j.el.addEventListener('pointerdown', () => setTimeout(() => term.focus(), 0));
  j.aoFechar = () => { obs.disconnect(); ws.close(); term.dispose(); api('/api/terminal/fechar', { id }).catch(() => {}); delete SALVO.terminais[id]; salvar(); };
}
async function renderAtividade(j) {
  j.corpo.innerHTML = `<div class="pagina"><h1>Atividade</h1><p class="sub">O que cada agente e cada ferramenta fez, do mais novo para o mais antigo.</p><div class="lista">${estadoCache.eventos.map((e) =>
    `<div class="linha-item" data-abrir="agente:${esc(e.agente)}" style="cursor:pointer">${sprite(e.agente, 20)}<div class="cresce"><b>${esc(nome(e.agente))}</b><small>${esc(e.tarefa || '')}</small></div><small>${esc(e.ts.slice(11, 16))}</small>${chipEstado(e.estado)}</div>`).join('') || '<div class="vazio">Sem atividade ainda.</div>'}</div></div>`;
}

// ------------------------------------------------------------------ atualizações (instalador/atualizacao.py)
async function renderAtualizacoes(j) {
  const d = await api('/api/app/atualizacoes');
  const c = d.consulta || {};
  const canal = { git: 'pasta do Git', estavel: 'estável', teste: 'teste' }[d.canal] || d.canal;
  const quando = (t) => (t ? `${ddmm(t)} às ${t.slice(11, 16)}` : 'nunca');
  const situacao = c.erro ? `<div class="faixa">${esc(c.erro)}</div>`
    : c.nova ? `<div class="faixa"><b>Versão nova: ${esc(c.versao)}</b> · ${esc(c.titulo || '')} <button class="bt pri mini" data-acao="atualizacao_aplicar">Atualizar agora</button></div>
      ${c.notas ? `<pre class="console" style="max-height:220px;overflow:auto;white-space:pre-wrap">${esc(c.notas)}</pre>` : ''}`
    : `<p>${d.ultima_verificacao ? (c.versao ? 'Você está na versão mais nova.' : esc(c.titulo || '')) : 'Ainda não procurou atualizações.'}</p>`;
  j.corpo.innerHTML = `<div class="pagina"><h1>Atualizações</h1>
    <p class="sub">Ciello OS <b>${esc(d.versao)}</b> · canal ${esc(canal)} · última verificação: ${esc(quando(d.ultima_verificacao))}</p>
    ${situacao}
    <div class="acoes"><button class="bt ${c.nova ? '' : 'pri'}" data-acao="atualizacao_verificar">${icone('atualizar')} Procurar agora</button></div>
    <p class="sub">${d.verificar_ao_abrir ? 'O ícone do Ciello OS procura sozinho ao abrir (a cada 12 horas).' : 'A procura automática está desligada.'}
    Os seus dados (leads, financeiro, rascunhos, estado) nunca são tocados; arquivos do programa que você editou ficam guardados em estado\\atualizacoes.
    Depois de atualizar, feche e abra o Ciello OS. Canal e procura automática: atalho <b>Atualizações do Ciello OS</b> no menu Iniciar do Windows.</p></div>`;
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
  // terminais só voltam se o processo ainda está rodando (o servidor pode ter sido reiniciado)
  let vivos = []; try { vivos = (await api('/api/terminais')).ids || []; } catch { /* sem servidor */ }
  const lista = (pedido ? pedido.split(',') : (SALVO.abertas.length ? SALVO.abertas : ['briefing']))
    .filter((k) => !k.startsWith('term:') || (!pedido && vivos.includes(k.slice(5))))
    .filter((k) => { const d = definicao(k); return d && !d.acao; }).slice(0, 6);
  lista.forEach((k) => abrir(k));
}
iniciar();
