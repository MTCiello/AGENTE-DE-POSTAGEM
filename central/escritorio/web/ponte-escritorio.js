/* Ponte do Escritório: roda dentro da página do pixel-agents (servida em /escritorio/ pelo Ciello OS) sem alterar o
   código dele. Só observa a conexão que já existe: aprende o nome de cada agente e, quando um personagem é clicado
   (o pixel-agents manda "focusAgent"), avisa a área de trabalho para abrir a janela daquele agente. */
(() => {
  'use strict';
  const Nativo = window.WebSocket;
  const nomes = new Map(); // id do agente -> nome do teammate (equipes do Claude Code)
  const ajudantes = new Map(); // id do agente -> Map(id da ferramenta Task -> descrição do subagente, ex. "sdr: follow-ups")

  const avisar = (dados) => { try { window.parent.postMessage({ ciello: 'escritorio', ...dados }, location.origin); } catch { /* fora do Ciello OS */ } };

  function recebido(m) {
    if (!m || typeof m !== 'object') return;
    if (m.type === 'existingAgents') {
      // retrato completo (também depois de o pixel-agents reiniciar e os ids recomeçarem): esquece o que sabia
      nomes.clear(); ajudantes.clear();
      for (const id of m.agents || []) {
        const meta = (m.agentMeta || {})[id] || {};
        if (meta.agentName || meta.teammateName) nomes.set(id, meta.agentName || meta.teammateName);
      }
    } else if (m.type === 'agentCreated') {
      if (m.teammateName) nomes.set(m.id, m.teammateName);
    } else if (m.type === 'agentTeamInfo') {
      if (m.agentName) nomes.set(m.id, m.agentName);
    } else if (m.type === 'agentToolStart') {
      const st = String(m.status || '');
      if (st.startsWith('Subtask:')) {
        if (!ajudantes.has(m.id)) ajudantes.set(m.id, new Map());
        ajudantes.get(m.id).set(m.toolId, st.slice(8).trim());
      }
    } else if (m.type === 'subagentClear') {
      const rotulo = ajudantes.get(m.id)?.get(m.parentToolId);
      ajudantes.get(m.id)?.delete(m.parentToolId);
      if (rotulo) avisar({ evento: 'terminou', rotulos: [rotulo] });
    } else if (m.type === 'agentToolsClear') {
      // fim do turno ou Esc: o pixel-agents limpa os subagentes sem mandar subagentClear (os de 2º plano voltam em seguida)
      const rotulos = [...(ajudantes.get(m.id) || new Map()).values()];
      ajudantes.delete(m.id);
      if (rotulos.length) avisar({ evento: 'terminou', rotulos });
    } else if (m.type === 'agentClosed') {
      nomes.delete(m.id); ajudantes.delete(m.id);
    }
    if (m.type === 'agentCreated' || m.type === 'agentClosed' || m.type === 'existingAgents') avisar({ evento: 'equipe', agentes: nomes.size });
  }

  class Ponte extends Nativo {
    constructor(url, protocolos) {
      super(url, protocolos);
      if (/\/ws(\?|$)/.test(String(url))) {
        this.addEventListener('message', (e) => { try { recebido(JSON.parse(e.data)); } catch { /* mensagem que não é JSON */ } });
      }
    }

    send(dado) {
      try {
        const m = JSON.parse(dado);
        if (m && m.type === 'focusAgent') {
          avisar({ evento: 'clique', id: m.id, nome: nomes.get(m.id) || '', ajudantes: [...(ajudantes.get(m.id) || new Map()).values()] });
        }
      } catch { /* não é JSON: segue normal */ }
      super.send(dado);
    }
  }
  window.WebSocket = Ponte;

  // ------------------------------------------------------------------ aparência: fundo azul da Ciello e controles escondidos
  // Os botões de personalização (+ Agente, Layout, Configurações, zoom, versão) só aparecem quando a engrenagem
  // da barra de tarefas do Ciello OS liga a classe "ciello-controles".
  const estilo = document.createElement('style');
  estilo.textContent = `
    html, body, .bg-bg:has(> canvas) { background: linear-gradient(160deg, #2C4469 0%, #263A59 45%, #13213A 100%) !important; }
    html:not(.ciello-controles) .absolute.left-10.bottom-10.z-20.pixel-panel,
    html:not(.ciello-controles) .absolute.top-8.left-8.z-10,
    html:not(.ciello-controles) .absolute.bottom-8.right-28,
    html:not(.ciello-controles) .pixel-panel.max-w-2xs.cursor-pointer { display: none !important; }`;
  document.documentElement.appendChild(estilo);
  window.addEventListener('message', (e) => {
    if (e.source !== window.parent || e.origin !== location.origin || !e.data) return;
    if (e.data.ciello === 'controles') document.documentElement.classList.toggle('ciello-controles', !!e.data.ligado);
    if (e.data.ciello === 'centralizar') centralizar();
  });

  // ------------------------------------------------------------------ centralizar: acha o escritório no desenho e arrasta
  // com o botão do meio (o mesmo gesto do pixel-agents), o que também solta a câmera que seguia alguém
  function centralizar() {
    const c = document.querySelector('.bg-bg > canvas');
    if (!c || !c.width) return;
    let d;
    try { d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; } catch { return; }
    const W = c.width, H = c.height;
    let x0 = W, x1 = -1, y0 = H, y1 = -1;
    for (let y = 0; y < H; y += 4) for (let x = 0; x < W; x += 4) {
      if (d[(y * W + x) * 4 + 3] > 0) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
    }
    if (x1 < 0) return;
    const dpr = window.devicePixelRatio || 1, r = c.getBoundingClientRect();
    const dx = (W / 2 - (x0 + x1) / 2) / dpr, dy = (H / 2 - (y0 + y1) / 2) / dpr;
    if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return;
    const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    const ev = (tipo, x, y) => c.dispatchEvent(new MouseEvent(tipo, { bubbles: true, cancelable: true, button: 1, buttons: tipo === 'mouseup' ? 0 : 4, clientX: x, clientY: y }));
    ev('mousedown', cx, cy); ev('mousemove', cx + dx / 2, cy + dy / 2); ev('mousemove', cx + dx, cy + dy); ev('mouseup', cx + dx, cy + dy);
  }

  // ------------------------------------------------------------------ português do Brasil (só o que aparece na tela)
  const { textos = {}, moldes = [] } = self.PIXEL_PTBR || {};
  function traduzir(t) {
    const nu = t.trim();
    if (!nu) return null;
    let r = Object.prototype.hasOwnProperty.call(textos, nu) ? textos[nu] : undefined;
    if (r === undefined && Object.prototype.hasOwnProperty.call(textos, t)) return textos[t] === t ? null : textos[t];
    if (r === undefined) for (const [re, troca] of moldes) if (re.test(nu)) { r = nu.replace(re, troca); break; }
    return r === undefined || r === nu ? null : t.replace(nu, r);
  }
  const ATRIBUTOS = ['title', 'placeholder', 'aria-label'];
  const ignorar = (n) => n.parentElement && n.parentElement.closest('.xterm, script, style, textarea');
  function varrer(raiz) {
    if (!raiz) return;
    if (raiz.nodeType === Node.TEXT_NODE) {
      if (!ignorar(raiz)) { const n = traduzir(raiz.nodeValue); if (n !== null) raiz.nodeValue = n; }
      return;
    }
    if (raiz.nodeType !== Node.ELEMENT_NODE || raiz.closest('.xterm')) return;
    const w = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT);
    while (w.nextNode()) { const nd = w.currentNode; if (!ignorar(nd)) { const n = traduzir(nd.nodeValue); if (n !== null) nd.nodeValue = n; } }
    for (const el of [raiz, ...raiz.querySelectorAll('[title],[placeholder],[aria-label]')]) {
      for (const at of ATRIBUTOS) { const v = el.getAttribute && el.getAttribute(at); if (v) { const n = traduzir(v); if (n !== null) el.setAttribute(at, n); } }
    }
  }

  // ------------------------------------------------------------------ zoom: Ctrl + scroll, entre ZOOM_MIN e ZOOM_MAX
  // O pixel-agents vai de 1x a 10x. Aqui o Ctrl + scroll (e os botões de zoom) ficam entre 2x e 6x.
  const ZOOM_MIN = 2, ZOOM_MAX = 6;
  let zoom = null, acumulado = 0, interno = false;
  const botoesZoom = () => { const c = document.querySelector('.absolute.top-8.left-8.z-10'); const b = c ? c.querySelectorAll('button') : []; return { mais: b[0], menos: b[1] }; };
  const espera = (ms) => new Promise((r) => setTimeout(r, ms));
  const clicar = (b) => { interno = true; try { b.click(); } finally { interno = false; } };
  function lerIndicador() { // o pixel-agents mostra "3x" no alto da tela a cada mudança de zoom
    const el = [...document.querySelectorAll('.pixel-panel')].find((e) => /^\d+\s*x$/.test(e.textContent.trim()));
    return el ? parseInt(el.textContent, 10) : null;
  }
  async function acertarZoom() {
    const { mais, menos } = botoesZoom();
    if (!mais || !menos) return false;
    if (mais.disabled) zoom = 10;
    else { clicar(mais); await espera(120); clicar(menos); await espera(120); zoom = lerIndicador(); }
    if (zoom === null) return false;
    while (zoom < ZOOM_MIN) { clicar(botoesZoom().mais); zoom++; await espera(60); }
    while (zoom > ZOOM_MAX) { clicar(botoesZoom().menos); zoom--; await espera(60); }
    return true;
  }
  window.addEventListener('wheel', (e) => {
    if (!(e.ctrlKey || e.metaKey)) return; // scroll comum: o pixel-agents move o escritório
    e.preventDefault(); e.stopImmediatePropagation(); // nada de zoom do navegador; o zoom é o do escritório
    acumulado += e.deltaY;
    if (Math.abs(acumulado) < 50 || zoom === null) return;
    const passo = acumulado < 0 ? 1 : -1; acumulado = 0;
    const novo = zoom + passo;
    if (novo < ZOOM_MIN || novo > ZOOM_MAX) return;
    const { mais, menos } = botoesZoom();
    const b = passo > 0 ? mais : menos;
    if (b && !b.disabled) { clicar(b); zoom = novo; }
  }, { capture: true, passive: false });
  // os botões + e − (visíveis com a engrenagem) respeitam os mesmos limites
  window.addEventListener('click', (e) => {
    if (interno || zoom === null) return;
    const { mais, menos } = botoesZoom();
    const b = e.target.closest && e.target.closest('button');
    if (!b || (b !== mais && b !== menos)) return;
    const novo = zoom + (b === mais ? 1 : -1);
    if (novo < ZOOM_MIN || novo > ZOOM_MAX) { e.preventDefault(); e.stopImmediatePropagation(); return; }
    zoom = novo;
  }, true);

  // ------------------------------------------------------------------ observa a página do pixel-agents
  let zoomPronto = false;
  const observador = new MutationObserver((mudancas) => {
    for (const m of mudancas) {
      if (m.type === 'characterData') varrer(m.target);
      else if (m.type === 'attributes') varrer(m.target);
      else m.addedNodes.forEach(varrer);
    }
    const ind = lerIndicador(); if (ind !== null && !interno) zoom = ind; // mantém o zoom em dia
    if (!zoomPronto && botoesZoom().mais) {
      zoomPronto = true;
      setTimeout(() => acertarZoom().then((ok) => { if (!ok) zoomPronto = false; else setTimeout(centralizar, 900); }), 600);
    }
  });
  const comecar = () => {
    varrer(document.body);
    observador.observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ATRIBUTOS });
  };
  if (document.body) comecar(); else document.addEventListener('DOMContentLoaded', comecar);
})();
