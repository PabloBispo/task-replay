# Os cinco caminhos

## A · API oficial

Procure na documentação do sistema, no rodapé ("desenvolvedores", "integração", "webservice") e na web. Muitos ERPs, emissores de nota e bancos têm API. API oficial é estável, documentada e permitida. Use `httpx` com a autenticação que ela pede.

## B · httpx + BeautifulSoup

O caso mais comum e o mais barato. O script repete as requisições que o navegador faz.

Padrões:

- **Uma sessão só.** `httpx.Client(follow_redirects=True)` guarda os cookies entre as chamadas.
- **Cabeçalhos realistas.** Copie do HAR o `User-Agent`, o `Accept-Language` e o `Referer` quando o servidor exigir.
- **Campos ocultos.** Antes de cada POST, faça o GET da página do formulário e extraia todos os `<input type="hidden">`:

```python
def campos_ocultos(html):
    soup = BeautifulSoup(html, "html.parser")
    return {i["name"]: i.get("value", "")
            for i in soup.select("input[type=hidden]") if i.get("name")}
```

- **Reaproveitar a sessão do navegador.** Se o login foi feito no Playwright (caminho D), carregue os cookies de `sessao/estado.json`:

```python
import json, httpx
estado = json.load(open("sessao/estado.json"))
client = httpx.Client(follow_redirects=True)
for c in estado["cookies"]:
    client.cookies.set(c["name"], c["value"], domain=c["domain"], path=c["path"])
```

- **Detectar sessão expirada.** Se a resposta redireciona para a tela de login ou contém o formulário de login, pare com a mensagem "sessão expirada, rode o login de novo". Não tente logar sozinho se houver captcha.
- **Ritmo humano.** Pausa de 1 a 3 segundos entre itens. Não dispare requisições em paralelo contra sistema de terceiros.

Modelo completo em `templates/script_httpx.py`.

## C · Playwright headless

Quando o site monta as requisições no JavaScript de um jeito que não dá para reproduzir.

- Use seletores estáveis, nesta ordem: `get_by_role` e `get_by_label` (texto visível), `data-testid`, `id`. Evite caminhos CSS longos e XPath posicional.
- Espere pelo resultado, não por tempo: `expect(page.get_by_text("Nota emitida")).to_be_visible()`.
- Mesmo no Playwright, dá para interceptar a resposta JSON (`page.expect_response`) e ler os dados direto, em vez de raspar a tela.
- Rode com `headless=True` no dia a dia e `headless=False` para depurar.

Modelo completo em `templates/script_playwright.py`.

## D · Login assistido (captcha, 2FA, certificado)

O humano entra só no login. O resto continua automático.

1. O script tenta usar `sessao/estado.json`.
2. Se a sessão não existe ou expirou, abre o navegador **visível** na tela de login e espera.
3. O usuário faz o login, resolve o captcha ou o 2FA e aperta Enter no terminal.
4. O script salva o novo `estado.json` e segue em modo headless (C) ou passa os cookies para o `httpx` (B).

Certificado digital A1 (arquivo `.pfx`): o `httpx` aceita certificado de cliente. Converta o `.pfx` para `.pem` com `openssl`, guarde fora do repositório e passe via `httpx.Client(cert=(...))`. A senha do certificado vai no `.env`. Certificado A3 (token ou cartão) depende do navegador: use o login assistido.

Nunca use serviço de quebra de captcha. Além de violar os termos da maioria dos sites, não é necessário: a sessão salva costuma durar horas ou dias.

## E · Mapa executado pelo Haiku

Último recurso. Cada execução ainda gasta print, mas com o modelo mais barato e sem precisar pensar.

Formato de cada passo no `mapa.md`:

```
### Passo 7 · Preencher valor do serviço
- Tela: Emissão de NFS-e › Serviços (URL: /nfse/emitir/servicos)
- Elemento: campo com o rótulo "Valor do serviço" (seletor: #valorServico)
- Ação: digitar
- Valor: {valor} da linha atual do CSV, formato 1234,56
- Depois: o campo "Valor líquido" é recalculado sozinho
- Se der errado: parar e reportar o print da tela
```

Instrução para o subagente executor:

```
Você executa o mapa.md passo a passo, sem improvisar.
Use só os valores da linha atual do CSV.
Se a tela não bater com o "Depois" do passo, pare e reporte.
No passo marcado CONFIRMAR, pare e peça confirmação ao usuário.
```

Quando o mesmo passo falhar duas vezes, ele volta para o modelo inteligente remapear.

## Quando não automatizar

- A tarefa acontece menos de uma vez por mês e leva poucos minutos.
- Os termos do sistema proíbem automação e o usuário não quer correr o risco.
- Cada execução exige decisão humana diferente (não é repetição, é julgamento).

Nesses casos, entregue só o `mapa.md` como checklist para o humano.
