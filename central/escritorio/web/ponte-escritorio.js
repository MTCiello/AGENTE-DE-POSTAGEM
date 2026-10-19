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

  // o espaço em volta do escritório fica no azul da Ciello
  const estilo = document.createElement('style');
  estilo.textContent = 'html, body { background: #1B2B45 !important; }';
  document.documentElement.appendChild(estilo);
})();
