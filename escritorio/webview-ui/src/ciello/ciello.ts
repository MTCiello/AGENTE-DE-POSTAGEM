/**
 * Ciello OS: o escritório roda dentro da área de trabalho do Ciello OS (num iframe, mesmo endereço).
 *
 * - A engrenagem da barra de tarefas mostra e esconde os controles (+ Agente, Layout, Configurações, zoom).
 * - "Centralizar escritório" no menu Iniciar volta a câmera para o meio.
 * - Clicar num personagem avisa a área de trabalho, que abre a janela daquele agente.
 *
 * Fora do Ciello OS (página aberta sozinha) os controles ficam sempre à vista.
 */
import { transport } from '../transport/index.js';

export const noCielloOS = typeof window !== 'undefined' && window.parent !== window;

type Ouvinte = () => void;

// ── engrenagem e centralizar (mensagens da área de trabalho) ───────────────────

let controles = !noCielloOS;
const ouvintesControles = new Set<Ouvinte>();
const ouvintesCentralizar = new Set<Ouvinte>();

if (noCielloOS) {
  // Ctrl + scroll é o zoom do escritório (o canvas cuida); em cima dos menus, não deixa virar zoom da página
  window.addEventListener(
    'wheel',
    (e: WheelEvent) => {
      if (e.ctrlKey || e.metaKey) e.preventDefault();
    },
    { passive: false },
  );
  window.addEventListener('message', (e: MessageEvent) => {
    if (e.source !== window.parent || e.origin !== location.origin || !e.data) return;
    const dados = e.data as { ciello?: string; ligado?: boolean };
    if (dados.ciello === 'controles') {
      controles = !!dados.ligado;
      ouvintesControles.forEach((f) => f());
    } else if (dados.ciello === 'centralizar') {
      ouvintesCentralizar.forEach((f) => f());
    }
  });
}

/** Para useSyncExternalStore: os controles estão à vista? */
export function assinarControles(f: Ouvinte): () => void {
  ouvintesControles.add(f);
  return () => ouvintesControles.delete(f);
}
export const controlesVisiveis = (): boolean => controles;

export function aoCentralizar(f: Ouvinte): () => void {
  ouvintesCentralizar.add(f);
  return () => ouvintesCentralizar.delete(f);
}

// ── quem é quem (para a janela certa abrir no clique) ──────────────────────────

const nomes = new Map<number, string>(); // id do agente -> nome do teammate (equipes do Claude Code)
const ajudantes = new Map<number, Map<string, string>>(); // id -> (ferramenta Task -> "sdr: follow-ups")

function avisar(dados: Record<string, unknown>): void {
  if (!noCielloOS) return;
  try {
    window.parent.postMessage({ ciello: 'escritorio', ...dados }, location.origin);
  } catch {
    /* área de trabalho indisponível */
  }
}

transport.onMessage((m) => {
  const msg = m as unknown as Record<string, unknown> & { type: string; id: number };
  switch (msg.type) {
    case 'existingAgents':
      // retrato completo (também depois de o servidor reiniciar e os ids recomeçarem)
      nomes.clear();
      ajudantes.clear();
      break;
    case 'agentCreated':
      if (typeof msg.teammateName === 'string') nomes.set(msg.id, msg.teammateName);
      break;
    case 'agentTeamInfo':
      if (typeof msg.agentName === 'string') nomes.set(msg.id, msg.agentName);
      break;
    case 'agentToolStart': {
      const st = String(msg.status ?? '');
      if (st.startsWith('Subtask:')) {
        if (!ajudantes.has(msg.id)) ajudantes.set(msg.id, new Map());
        ajudantes.get(msg.id)!.set(String(msg.toolId), st.slice(8).trim());
      }
      break;
    }
    case 'subagentClear': {
      const rotulo = ajudantes.get(msg.id)?.get(String(msg.parentToolId));
      ajudantes.get(msg.id)?.delete(String(msg.parentToolId));
      if (rotulo) avisar({ evento: 'terminou', rotulos: [rotulo] });
      break;
    }
    case 'agentToolsClear': {
      // fim da vez ou Esc: os subagentes somem sem subagentClear (os de segundo plano voltam em seguida)
      const rotulos = [...(ajudantes.get(msg.id)?.values() ?? [])];
      ajudantes.delete(msg.id);
      if (rotulos.length) avisar({ evento: 'terminou', rotulos });
      break;
    }
    case 'agentClosed':
      nomes.delete(msg.id);
      ajudantes.delete(msg.id);
      break;
  }
  if (msg.type === 'agentCreated' || msg.type === 'agentClosed' || msg.type === 'existingAgents') {
    avisar({ evento: 'equipe', agentes: nomes.size });
  }
});

/** + Agente: a área de trabalho abre o terminal do Claude Code dentro do Ciello OS. */
export function pedirNovoAgente(): void {
  avisar({ evento: 'novoAgente' });
}

/** Personagem clicado: a área de trabalho abre a janela do agente (ou de quem trabalha com ele). */
export function avisarClique(id: number): void {
  avisar({ evento: 'clique', id, nome: nomes.get(id) ?? '', ajudantes: [...(ajudantes.get(id)?.values() ?? [])] });
}
