/* Tradução do pixel-agents 1.5.0 para o português do Brasil. A ponte (ponte-escritorio.js) troca só o texto que
   aparece na tela; as mensagens entre o escritório e o servidor continuam em inglês, porque o pixel-agents depende
   delas ("Reading", "Subtask:"...). Ao atualizar o pixel-agents, rode a coleta de textos e complete o que faltar. */
self.PIXEL_PTBR = {
  textos: {
    // barra de baixo, zoom e cabeçalhos
    '+ Agent': '+ Agente', 'Layout': 'Layout', 'Settings': 'Configurações', 'Edit office layout': 'Editar o layout do escritório',
    'Zoom in (Ctrl+Scroll)': 'Aproximar (Ctrl + scroll)', 'Zoom out (Ctrl+Scroll)': 'Afastar (Ctrl + scroll)',
    'Office': 'Escritório', 'Show office': 'Mostrar escritório', 'Show terminal': 'Mostrar terminal', 'Launch agent': 'Abrir agente',
    'Close': 'Fechar', 'Close agent': 'Fechar agente', 'Close terminal': 'Fechar terminal', 'Loading...': 'Carregando…',
    'Terminal unavailable': 'Terminal indisponível', 'Terminal unavailable on this server.': 'Terminal indisponível neste servidor.',
    'No agent terminals yet': 'Nenhum terminal de agente ainda', 'Tap + in the bar below to launch one': 'Toque no + da barra abaixo para abrir um',
    // estados dos personagens
    'Needs approval': 'Precisa de aprovação', 'Waiting for input': 'Esperando resposta', 'Idle': 'Livre', 'Subtask': 'Subtarefa', 'Subtask:': 'Subtarefa:', 'Task': 'Tarefa',
    // apresentação (onboarding)
    'Welcome to Pixel Agents!': 'Bem-vindo ao escritório!',
    "In this office, your AI agents become tiny pixel characters: they type at their desks while they work, wander off when they're done, and speak up when they need you.":
      'Neste escritório, seus agentes de IA viram personagens em pixel: digitam na mesa enquanto trabalham, passeiam quando terminam e avisam quando precisam de você.',
    'The office watches your Claude Code sessions and brings them to life in here. New to Claude Code? Download it first:':
      'O escritório acompanha suas sessões do Claude Code e dá vida a elas aqui. Ainda não usa o Claude Code? Baixe primeiro:',
    'For more info, visit': 'Para saber mais, acesse',
    'One more thing: hooks!': 'Só mais uma coisa: os hooks!',
    'To bring your agents to life in real time, Pixel Agents adds hooks for 12 Claude Code events to ~/.claude/settings.json. Note that your existing settings are kept, and a one-time backup is saved as settings.json.pixel-agents.backup.':
      'Para os agentes ganharem vida em tempo real, o escritório adiciona hooks para 12 eventos do Claude Code em ~/.claude/settings.json. Suas configurações atuais são mantidas, e uma cópia de segurança é salva uma única vez como settings.json.pixel-agents.backup.',
    'Claude Code will send those events - including tool names and tool inputs - to a Pixel Agents server on this machine. Everything stays local - the server listens only on 127.0.0.1 - unless you explicitly start it with --host to expose it on your network.':
      'O Claude Code vai mandar esses eventos (inclusive o nome e os dados das ferramentas) para o servidor do escritório nesta máquina. Tudo fica no seu PC: o servidor só escuta em 127.0.0.1, a não ser que você o inicie com --host para abrir na sua rede.',
    'You can remove the hooks at any time from Settings → Instant Detection (Hooks).': 'Você pode remover os hooks quando quiser em Configurações → Detecção instantânea (hooks).',
    'This works through Claude Code Hooks, small event listeners that notify Pixel Agents whenever something happens in your Claude sessions.':
      'Isso funciona com os hooks do Claude Code: pequenos avisos que contam ao escritório tudo o que acontece nas suas sessões do Claude.',
    "You're all set!": 'Tudo pronto!',
    'Enjoy your new office! Questions, ideas, or pixel art to show off? Come hang out in our Discord.': 'Aproveite o seu escritório novo! Dúvidas, ideias ou pixel art para mostrar? Venha para o nosso Discord.',
    'Join our Discord!': 'Entre no nosso Discord!',
    'Install Hooks': 'Instalar hooks', 'Not Now': 'Agora não', "Don't Ask Again": 'Não perguntar de novo', "Let's Go": 'Vamos lá', 'Continue': 'Continuar',
    'Back': 'Voltar', 'Got it': 'Entendi', 'Yes': 'Sim', 'No': 'Não', 'Cancel': 'Cancelar', 'Save': 'Salvar', 'Delete': 'Excluir', 'Add': 'Adicionar',
    'Copy': 'Copiar', 'Reset': 'Restaurar', 'Reset?': 'Restaurar?', 'View more': 'Ver mais', 'View only': 'Só visualizar', 'View on GitHub': 'Ver no GitHub',
    'Your Pixel Agents office now reacts in real-time:': 'Seu escritório agora reage em tempo real:', 'Your agents now respond in real-time.': 'Seus agentes agora respondem em tempo real.',
    'Permission prompts appear instantly': 'Pedidos de permissão aparecem na hora', 'Turn completions detected the moment they happen': 'O fim de cada resposta aparece na hora',
    'Sound notifications play immediately': 'O som de aviso toca na hora', 'To disable, go to Settings ': 'Para desligar, vá em Configurações ', ' Instant Detection': ' Detecção instantânea',
    'Something went wrong writing to your Claude Code settings, so the office will watch your sessions the slower way instead. No worries, everything still works and you can retry activating them any time from Settings.':
      'Não deu para gravar nas configurações do Claude Code, então o escritório vai acompanhar as sessões pelo jeito mais lento. Tudo continua funcionando, e você pode tentar ativar de novo em Configurações.',
    // novidades e pedido de desculpas da versão
    'See what\'s new': 'Ver as novidades', "See what's new!": 'Ver as novidades!', 'Updated to v': 'Atualizado para a v', "What's New in v": 'Novidades da v',
    'Features': 'Recursos', 'Fixes': 'Correções', 'Maintenance': 'Manutenção', 'Testing': 'Testes', 'Changes': 'Mudanças', 'Contributors': 'Colaboradores',
    'We owe you an apology!': 'Devemos um pedido de desculpas!', "We're really sorry about that.": 'Sentimos muito por isso.',
    "We've just migrated to fully open-source assets, all built from scratch with love. Unfortunately, this means your previous layout had to be reset.":
      'Acabamos de migrar para gráficos 100% abertos, feitos do zero com carinho. Por isso, o seu layout anterior precisou ser restaurado.',
    'The good news? This was a one-time thing, and it paves the way for some genuinely exciting updates ahead.': 'A boa notícia: isso aconteceu uma única vez e abre caminho para novidades bem legais.',
    'Stay tuned, and thanks for using Pixel Agents!': 'Fique de olho, e obrigado por usar o Pixel Agents!',
    'Standalone and Architecture': 'Modo independente e arquitetura', 'Testing and Release Infrastructure': 'Testes e infraestrutura de lançamento',
    'Agent diagnostics, JSONL resilience, CI improvements': 'Diagnóstico dos agentes, JSONL mais robusto, melhorias de CI',
    'Animated pet system, bundled pet sprites, and pet interactions': 'Bichinhos animados, sprites incluídos e interações com eles',
    'Architecture, Agent Teams, standalone, multi-server, file-watcher and CI hardening, e2e, and release work': 'Arquitetura, equipes de agentes, modo independente, vários servidores, observador de arquivos, CI, testes e lançamentos',
    'Carpet system and foundational Playwright e2e infrastructure': 'Tapetes e a base dos testes de ponta a ponta com Playwright',
    'Claude 2.1.220 sub-agents and teammates, context gauge, Workspace Areas, layout-editor polish, narrated e2e review': 'Subagentes e teammates do Claude 2.1.220, medidor de contexto, áreas de trabalho, editor de layout refinado e revisão narrada',
    'Claude Code hooks integration, Tailwind v4 migration': 'Integração com os hooks do Claude Code e migração para o Tailwind v4',
    'Cross-platform Windows build script and server test isolation': 'Build para Windows e testes do servidor isolados',
    'Custom characters from external asset directories': 'Personagens próprios a partir de pastas de gráficos externas',
    'Duplicate restore, tool status reconnect, tool detection fixes': 'Correções de restauração duplicada, reconexão e detecção de ferramentas',
    'Early Agent Teams implementation that informed the shipped design': 'Primeira versão das equipes de agentes, que guiou o desenho final',
    'Embedded terminal, mobile web app, agent cards, Directories, and layout editor upgrades': 'Terminal embutido, app para celular, cartões de agente, pastas e editor de layout melhorado',
    'External asset packs support': 'Pacotes de gráficos externos', 'External session support and Agent tool recognition': 'Sessões externas e reconhecimento da ferramenta Agent',
    'Hooks-first dual-mode architecture, review coordination': 'Arquitetura com hooks em primeiro lugar e coordenação de revisões',
    'Linux/macOS fix for no-folder workspaces': 'Correção no Linux/macOS para espaços de trabalho sem pasta',
    'Multi-root workspace agent detection': 'Detecção de agentes em espaços de trabalho com várias pastas',
    'Playwright e2e tests, browser preview mode': 'Testes de ponta a ponta com Playwright e modo de pré-visualização no navegador',
    'Reported the hook-install and restored-agent rendering bugs': 'Relatou os erros de instalação dos hooks e de desenho de agentes restaurados',
    'Restored-agent rendering fix': 'Correção no desenho de agentes restaurados', 'Standalone rendering fix for agents that already exist on connect': 'Correção no modo independente para agentes que já existiam ao conectar',
    'Workspace JSONL discovery with hooks enabled': 'Descoberta de JSONL do espaço de trabalho com hooks ligados',
    // configurações
    'Instant Detection (Hooks)': 'Detecção instantânea (hooks)', 'Instant Detection Active': 'Detecção instantânea ativa', 'Instant Detection is ON': 'Detecção instantânea LIGADA',
    'Watch All Sessions': 'Acompanhar todas as sessões', 'Sound Notifications': 'Aviso sonoro', 'Always Show Labels': 'Sempre mostrar os nomes',
    'Always show overlay setting': 'Sempre mostrar as informações', 'Always show overlay setting for agent labels': 'Sempre mostrar o nome dos agentes',
    'Show Areas': 'Mostrar áreas', 'Show Start Directory': 'Mostrar a pasta inicial', 'Skip Permissions': 'Pular permissões', 'Bypass permissions mode': 'Modo sem pedir permissão',
    'Debug View': 'Modo de diagnóstico', 'Display Headless as Ghosts': 'Mostrar sessões sem terminal como fantasmas', 'Export Layout': 'Exportar layout', 'Import Layout': 'Importar layout',
    'Open Sessions Folder': 'Abrir a pasta das sessões', 'Automatic panel display and agent startup settings': 'Abertura automática do painel e início dos agentes',
    'Add Asset Directory': 'Adicionar pasta de gráficos', 'Absolute asset directory path': 'Caminho completo da pasta de gráficos', 'Edit directory': 'Editar pasta',
    '+ Directory': '+ Pasta', 'Recent working directories': 'Pastas de trabalho recentes', 'Project name': 'Nome do projeto', 'Name': 'Nome', 'Path': 'Caminho',
    'Project dir does not exist: ': 'A pasta do projeto não existe: ', 'JSONL connected': 'JSONL conectado', 'JSONL not found': 'JSONL não encontrado', 'Lines: ': 'Linhas: ', 'Last data: ': 'Último dado: ',
    'File has data (': 'O arquivo tem dados (', ' bytes) but 0 lines parsed. Possible format issue.': ' bytes), mas nenhuma linha foi lida. Pode ser problema de formato.',
    // áreas
    'Areas': 'Áreas', 'Add Area': 'Adicionar área', 'Add a new Area': 'Adicionar uma área nova', 'Area color': 'Cor da área', 'Area name…': 'Nome da área…', 'Remove area': 'Remover área',
    'No areas yet — add one above': 'Nenhuma área ainda: adicione uma acima', 'No folders mapped': 'Nenhuma pasta ligada', 'Map a folder…': 'Ligar uma pasta…', 'Add folder…': 'Adicionar pasta…',
    'All folders already mapped': 'Todas as pastas já estão ligadas', 'Unmap folder': 'Desligar pasta',
    'Define folder-bound areas — agents spawn in their folder\'s area': 'Defina áreas ligadas a pastas: cada agente aparece na área da pasta dele',
    "Paint areas on the map, then assign workspace folders. Agents will sit in their folder's area.": 'Pinte as áreas no mapa e depois ligue as pastas de trabalho. Os agentes vão sentar na área da pasta deles.',
    // editor de layout
    'Floor': 'Piso', 'Wall': 'Parede', 'Walls': 'Paredes', 'Furniture': 'Móveis', 'Carpet': 'Tapete', 'Pets': 'Bichinhos', 'Erase': 'Apagar',
    'Desks': 'Mesas', 'Chairs': 'Cadeiras', 'Decor': 'Decoração', 'Misc': 'Diversos', 'Storage': 'Armários', 'Tech': 'Eletrônicos', 'Main': 'Principal', 'Accent': 'Detalhe',
    'Color': 'Cor', 'Colorize': 'Colorir', 'Toggle colorize mode': 'Ligar ou desligar o modo colorir', 'Hue': 'Matiz', 'Saturation': 'Saturação', 'Brightness': 'Brilho', 'Contrast': 'Contraste',
    'Adjust floor color': 'Ajustar a cor do piso', 'Adjust wall color': 'Ajustar a cor da parede', 'Adjust carpet main + accent colors': 'Ajustar as cores do tapete',
    'Adjust color for new furniture': 'Ajustar a cor dos móveis novos', 'Paint floor tiles': 'Pintar o piso', 'Paint walls (click to toggle)': 'Pintar paredes (clique para pôr ou tirar)',
    'Paint carpets': 'Pintar tapetes', 'Place furniture': 'Colocar móveis', 'Place pets': 'Colocar bichinhos', 'Erase tiles to void': 'Apagar o piso',
    'Copy floor pattern + color from existing tile': 'Copiar o piso e a cor de um quadrado existente', 'Copy carpet variant + colors from existing tile (P)': 'Copiar o tapete e as cores de um quadrado existente (P)',
    'Copy furniture type from placed item': 'Copiar o tipo de um móvel já colocado', 'Copy color from another item — click one in the office': 'Copiar a cor de outro item: clique num item do escritório',
    'Undo': 'Desfazer', 'Undo (Ctrl+Z)': 'Desfazer (Ctrl+Z)', 'Redo': 'Refazer', 'Redo (Ctrl+Y)': 'Refazer (Ctrl+Y)', 'Rotate (R)': 'Girar (R)',
    'Save layout': 'Salvar layout', 'Reset to default': 'Voltar ao padrão', 'Reset to last saved layout': 'Voltar ao último layout salvo', 'Drag to resize': 'Arraste para mudar o tamanho',
    'Heart bubble: shown when a pet is petted (11x13)': 'Balão de coração: quando um bichinho recebe carinho (11x13)',
    "Permission bubble: white square with '...' in amber, and a tail pointer (11x13)": "Balão de permissão: quadrado branco com '...' em âmbar (11x13)",
    'Waiting bubble: white square with green checkmark, and a tail pointer (11x13)': 'Balão de espera: quadrado branco com visto verde (11x13)',
    '~/code/my-project': '~/codigo/meu-projeto',
  },
  // textos com partes que mudam
  moldes: [
    [/^Reading (.+)$/, 'Lendo $1'], [/^Editing (.+)$/, 'Editando $1'], [/^Writing (.+)$/, 'Escrevendo $1'], [/^Running: (.+)$/, 'Rodando: $1'],
    [/^Subtask: (.+)$/, 'Subtarefa: $1'], [/^Using (.+)$/, 'Usando $1'], [/^Searching web(.*)$/, 'Pesquisando na web$1'], [/^Searching(.*)$/, 'Procurando$1'],
    [/^Fetching(.*)$/, 'Baixando$1'], [/^Globbing(.*)$/, 'Listando arquivos$1'], [/^Step (\d+) of (\d+)$/, 'Passo $1 de $2'], [/^Agent (\d+)$/, 'Agente $1'],
    [/^Agent #$/, 'Agente nº '], [/^Floor (\d+)$/, 'Piso $1'], [/^Wall (\d+)$/, 'Parede $1'], [/^Carpet (\d+)$/, 'Tapete $1'], [/^Edit (.+)$/, 'Editar $1'],
    [/^(.+) — double-click to rename$/, '$1 (clique duas vezes para renomear)'],
    [/^(\d+)% context used \((\d+)k of (\d+)k tokens\)$/, '$1% do contexto usado ($2 mil de $3 mil tokens)'],
  ],
};
