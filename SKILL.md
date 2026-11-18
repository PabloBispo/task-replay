---
name: mapa-de-execucao
description: Transforma uma tarefa repetitiva feita no navegador (emitir nota, baixar relatório, preencher cadastro, conferir pedido) numa automação barata. Use quando o usuário quiser automatizar algo que faz toda semana num site ou sistema web, quando reclamar que o Claude gasta muitos tokens controlando o navegador, ou quando pedir para "mapear", "roteirizar" ou "transformar em script" um processo web.
---

# Mapa de Execução

Mapeie uma vez. Execute mil.

O modelo mais inteligente investiga o sistema **uma vez** e escolhe o jeito mais barato de repetir a tarefa. Na maioria dos casos o resultado é um script Python que roda sem gastar nenhum token. Quando não dá, o resultado é um mapa numerado que um modelo barato (Haiku) consegue seguir.

Clicar pelo navegador a cada execução é o **último** recurso, não o primeiro: cada passo exige um print da tela, e print é caro em token.

## Regras que valem em todas as fases

1. **Credenciais nunca passam pelo chat.** Senha, token e cookie vão para `.env` e para o arquivo de sessão local. Nunca escreva uma senha em código, log, `mapa.md` ou resposta. Se o usuário colar uma senha no chat, peça para ele colocar no `.env` e não repita o valor.
2. **Nada é enviado, emitido, pago ou apagado sem confirmação.** O script para antes do passo com consequência e pergunta. Esse passo é marcado como `CONFIRMAR` no mapa.
3. **API oficial antes de scraping.** Se o sistema tem API documentada, use a API.
4. **Termos de uso.** Antes de automatizar, procure se o sistema proíbe automação (termos, `robots.txt`, aviso no login). Se proibir, avise o usuário e deixe a decisão com ele.
5. **Dados ficam na máquina do usuário.** O script roda local. Não envie dados de clientes para serviços de terceiros.
6. **Captcha, 2FA e certificado digital são do humano.** Nunca tente quebrar captcha. O script pausa, o usuário resolve, e a sessão salva é reaproveitada.

## Fase 1 · Entrevista

Antes de abrir qualquer coisa, pergunte, uma pergunta por vez:

- Qual é a tarefa, do início ao fim, em linguagem simples?
- Com que frequência ela se repete e quantos itens por vez?
- Qual é o sistema (URL) e como é o login: usuário e senha, 2FA, captcha, certificado digital A1/A3?
- De onde vêm os dados de entrada (planilha, CSV, outro sistema, digitação)?
- Qual é o resultado esperado (PDF baixado, número de protocolo, status na tela)?
- Qual passo tem consequência real (enviar, emitir, pagar, apagar)?

Registre as respostas na seção "Contexto" do `mapa.md` (modelo em `templates/mapa.md`).

## Fase 2 · Reconhecimento (uma vez só)

O objetivo é descobrir **quais requisições HTTP** o site faz, não onde clicar. Detalhes e comandos em `references/reconhecimento.md`.

1. Abra o sistema com o Playwright em modo visível e grave o tráfego (`record_har_path`) enquanto o usuário, ou você, executa a tarefa **uma vez** com dados de teste. O login fica com o usuário.
2. Salve a sessão (`storage_state`) logo após o login.
3. Analise o HAR: ignore imagens, fontes, analytics. Liste as requisições que realmente fazem o trabalho: método, URL, parâmetros, corpo, cabeçalhos relevantes, tokens (CSRF, `__VIEWSTATE`, nonce) e de onde cada token vem.
4. Anote a ordem das chamadas e o que cada resposta devolve que a próxima precisa.

Se o usuário não puder rodar o reconhecimento agora, peça que ele exporte o HAR pelo DevTools do navegador (Network → Export HAR) e envie o arquivo, avisando que o HAR contém cookies e deve ser apagado depois.

## Fase 3 · Viabilidade

Classifique a tarefa e escolha o **primeiro** caminho que funcionar, nesta ordem. Explique a escolha ao usuário em uma ou duas frases.

| # | Situação | Caminho | Custo por execução |
|---|---|---|---|
| A | Existe API oficial | chamada direta à API | zero token |
| B | Requisições reproduzíveis (formulário renderizado no servidor, JSON interno, token extraível do HTML) | `httpx` + BeautifulSoup | zero token |
| C | Depende de JavaScript que não dá para reproduzir (assinatura no cliente, fluxo em SPA complexo) | Playwright headless | zero token |
| D | Login com captcha, 2FA ou certificado | B ou C, com login assistido: abre navegador visível, o humano resolve, a sessão é salva e reaproveitada até expirar | zero token, humano entra só no login |
| E | Instável, muda sempre ou impossível de mapear | `mapa.md` detalhado executado por um modelo barato | baixo, mas ainda gasta token por print |

Critérios práticos e exemplos de cada caminho em `references/caminhos.md`.

Se a tarefa for rara (menos de uma vez por mês) e curta, diga que talvez não compense automatizar.

## Fase 4 · Construção

Gere, na pasta do projeto do usuário:

- `mapa.md`: o processo documentado, passo a passo, com entradas, saídas, requisições e o passo `CONFIRMAR`. Serve para humano ler, para o Haiku executar no caminho E e para remapear quando quebrar.
- `executar.py`: o script, partindo de `templates/script_httpx.py` (caminho B) ou `templates/script_playwright.py` (caminhos C e D).
- `.env.example`: as variáveis necessárias, sem valores reais.
- `.gitignore` com `.env`, `sessao/` e `*.har`.
- `requirements.txt`.

O script deve: ler os dados de entrada de um CSV ou planilha, processar um item por vez, registrar o resultado de cada item em `resultado.csv`, parar com mensagem clara quando a sessão expirar, e ter a flag `--teste` que roda tudo até o passo `CONFIRMAR` sem executá-lo.

## Fase 5 · Teste

1. Rode com `--teste` e um item só. Mostre ao usuário o que seria enviado.
2. Só com o "ok" do usuário rode um item real.
3. Depois rode o lote.

## Fase 6 · Execução pelo Haiku (só no caminho E)

Quando o caminho for E, o `mapa.md` precisa ser autossuficiente: cada passo com a URL, o elemento (texto visível e seletor), a ação, o valor e o que deve aparecer na tela depois. Explique ao usuário como rodar:

- No Claude Code: um subagente com `model: haiku` que recebe o `mapa.md` e os dados do item, segue os passos sem improvisar e para no `CONFIRMAR`.
- Se o Haiku travar num passo, ele para e reporta. O modelo inteligente só entra para remapear aquele passo.

## Fase 7 · Manutenção

Quando o site mudar e o script quebrar, não refaça tudo. Rode o reconhecimento só no trecho que falhou, atualize o passo no `mapa.md` e no script, e registre a data da mudança no fim do `mapa.md`.

## Entrega final ao usuário

Termine com: o caminho escolhido e por quê, os arquivos gerados, o comando para rodar, quanto tempo e quantos tokens isso economiza por execução (estimativa simples: passos × ~2.000 tokens por print evitado; o valor real varia com o tamanho da tela e o modelo) e o que ainda depende dele (login, captcha, confirmação).
