/**
 * Traduz para o português o status de ferramenta que o servidor manda em inglês
 * ("Reading x", "Running: cmd", "Subtask: desc"...). O texto continua em inglês
 * no protocolo, porque o código depende dele (toolUtils.extractToolName,
 * useExtensionMessages com 'Subtask:'). Use esta função só na hora de mostrar
 * o status na tela, nunca antes de um código que analisa o status.
 */

const FIXOS: Record<string, string> = {
  'Searching files': 'Procurando arquivos',
  'Searching code': 'Procurando no código',
  'Fetching web content': 'Lendo página da web',
  'Searching the web': 'Pesquisando na web',
  'Running subtask': 'Rodando subtarefa',
  'Waiting for your answer': 'Esperando a sua resposta',
  Planning: 'Planejando',
  'Editing notebook': 'Editando notebook',
  'Creating team': 'Criando equipe',
  'Sending message': 'Enviando mensagem',
};

const MOLDES: Array<[RegExp, string]> = [
  [/^Reading (.*)$/s, 'Lendo $1'],
  [/^Editing (.*)$/s, 'Editando $1'],
  [/^Writing (.*)$/s, 'Escrevendo $1'],
  [/^Running: ?(.*)$/s, 'Rodando: $1'],
  [/^Subtask: ?(.*)$/s, 'Subtarefa: $1'],
  [/^Creating team: ?(.*)$/s, 'Criando equipe: $1'],
  [/^Using (.*)$/s, 'Usando $1'],
];

export function traduzirStatus(status: string): string {
  if (!status) return status;
  const fixo = FIXOS[status];
  if (fixo) return fixo;
  for (const [molde, troca] of MOLDES) {
    if (molde.test(status)) return status.replace(molde, troca);
  }
  // "-> destinatário" e qualquer texto desconhecido seguem como vieram.
  return status;
}
