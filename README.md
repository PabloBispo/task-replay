# Task Replay

**Mapeie uma vez. Execute mil.**

Skill para Claude que transforma uma tarefa repetitiva feita no navegador (emitir nota, baixar relatório, preencher cadastro, conferir pedido) numa automação que roda sem gastar token.

## O problema

Quando o Claude controla o seu navegador, ele tira um print da tela a cada passo para saber onde clicar. Cada print custa milhares de tokens. Uma tarefa de 50 passos, repetida todo dia, come a sua franquia sem você perceber, e com o modelo mais caro fazendo trabalho de apertar botão.

## O que a skill faz

O modelo inteligente investiga o sistema **uma vez** e escolhe o jeito mais barato de repetir a tarefa:

| Caminho | Quando | Custo por execução |
|---|---|---|
| A · API oficial | o sistema tem API | zero token |
| B · httpx + BeautifulSoup | dá para repetir as requisições do site | zero token |
| C · Playwright headless | o site depende de JavaScript | zero token |
| D · Login assistido | tem captcha, 2FA ou certificado | zero token, você entra só no login |
| E · Mapa para o Haiku | nada acima funciona | baixo, com o modelo mais barato |

No fim você recebe:

- `mapa.md`: o processo documentado passo a passo
- `executar.py`: o script, com modo `--teste`
- `.env.example`, `requirements.txt` e `.gitignore`

E três regras que não se quebram: senha nunca passa pelo chat, nada é enviado ou emitido sem a sua confirmação, e captcha é sempre resolvido por você.

## Como instalar

### Claude Code

```bash
git clone https://github.com/PabloBispo/task-replay ~/.claude/skills/task-replay
```

Abra o Claude Code e peça: "quero automatizar a emissão de nota fiscal no sistema X".

### Claude (web, desktop e celular)

1. Baixe o `task-replay.zip` na página de [Releases](https://github.com/PabloBispo/task-replay/releases).
2. Vá em **Customize › Skills**, clique em **+**, depois **Create skill** e **Upload a skill**.
3. Escolha o zip.

Precisa da execução de código ativada. Como o Claude na web roda num ambiente isolado, o script gerado é para você rodar no seu computador.

## Exemplo

A pasta [`exemplo/`](exemplo/) tem uma automação completa do caminho B contra um site de treino público ([quotes.toscrape.com](https://quotes.toscrape.com)): login com token CSRF, paginação e exportação para CSV.

```bash
cd exemplo
pip install httpx beautifulsoup4
python executar.py --teste entrada.csv
```

## Estrutura

```
SKILL.md                    o fluxo que o Claude segue
references/reconhecimento.md  como gravar e ler as requisições (HAR)
references/caminhos.md        os cinco caminhos em detalhe
templates/                  modelos do script, do mapa e do .env
exemplo/                    automação pronta para testar
```

## Responsabilidade

Automatize só sistemas em que você tem acesso legítimo e confira os termos de uso de cada um. Alguns sistemas (bancos, portais do governo) proíbem ou bloqueiam automação. A skill verifica e avisa, mas a decisão é sua.

---

Feito por [Pablo Bispo](https://instagram.com/bispo.ia) · [@bispo.ia](https://instagram.com/bispo.ia)

Licença MIT
