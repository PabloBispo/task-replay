# Reconhecimento: descobrir as requisições

O objetivo é trocar "onde clicar" por "o que o site manda para o servidor". Quem clica gasta print a cada passo. Quem manda a requisição direto não gasta nada.

## 1. Gravar a tarefa uma vez

Instale o mínimo:

```bash
pip install playwright httpx beautifulsoup4 python-dotenv
playwright install chromium
```

Rode o gravador abaixo. Ele abre um navegador visível, o usuário faz login e executa a tarefa uma vez com dados de teste, e no fim ele salva o tráfego (HAR) e a sessão.

```python
# gravar.py
import asyncio, sys
from pathlib import Path
from playwright.async_api import async_playwright

URL = sys.argv[1]
Path("sessao").mkdir(exist_ok=True)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context(record_har_path="sessao/gravacao.har",
                                        record_har_content="embed")
        page = await ctx.new_page()
        await page.goto(URL)
        input("Faça o login e a tarefa completa no navegador. Depois aperte Enter aqui. ")
        await ctx.storage_state(path="sessao/estado.json")
        await ctx.close()   # o HAR só é gravado ao fechar o contexto
        await browser.close()

asyncio.run(main())
```

```bash
python gravar.py https://sistema.exemplo.com.br
```

`sessao/` contém cookies. Ela vai para o `.gitignore` e é apagada quando não for mais necessária.

Alternativa sem Python: DevTools do navegador → aba Network → marcar "Preserve log" → fazer a tarefa → botão de exportar HAR.

## 2. Filtrar o HAR

O HAR traz tudo, inclusive imagens e analytics. Fique só com o que importa:

```python
# filtrar_har.py
import json, sys
from urllib.parse import urlparse

har = json.load(open(sys.argv[1]))
host = sys.argv[2]           # ex.: sistema.exemplo.com.br
ignorar = (".png", ".jpg", ".svg", ".woff", ".woff2", ".css", ".ico", ".gif", ".map")

for i, e in enumerate(har["log"]["entries"]):
    req, res = e["request"], e["response"]
    u = urlparse(req["url"])
    if host not in u.netloc or u.path.endswith(ignorar):
        continue
    tipo = res["content"].get("mimeType", "")
    corpo = (req.get("postData") or {}).get("text", "")[:300]
    print(f'{i:>3} {req["method"]:<6} {res["status"]} {u.path}?{u.query[:80]}  [{tipo[:30]}]')
    if corpo:
        print(f'      corpo: {corpo}')
```

```bash
python filtrar_har.py sessao/gravacao.har sistema.exemplo.com.br
```

Não imprima cabeçalhos `Cookie` e `Authorization` no chat.

## 3. Perguntas para cada requisição relevante

- É GET de página (HTML) ou chamada de dados (JSON/XHR)?
- Que parâmetros e campos de formulário ela leva? Quais vêm dos dados do usuário e quais são fixos?
- Tem token? De onde ele vem: um `<input type="hidden">` da página anterior, um cookie, um cabeçalho de resposta, uma variável no JavaScript?
- O que a resposta devolve que a próxima requisição usa (id, protocolo, link do PDF)?
- Qual requisição é a que tem consequência (POST de emitir, enviar, pagar)? Ela vira o passo `CONFIRMAR`.

## 4. Sinais para escolher o caminho

- Respostas JSON limpas em `/api/...` → caminho B, chamando o JSON direto. Verifique antes se essa API é pública e documentada (caminho A).
- Formulários HTML com `csrf_token`, `__VIEWSTATE`, `__EVENTVALIDATION` (sites ASP.NET, comuns em prefeituras) → caminho B, extraindo os campos ocultos com BeautifulSoup antes de cada POST.
- Parâmetros assinados ou gerados no navegador (hash, timestamp criptografado, token que não aparece em nenhuma resposta) → caminho C.
- reCAPTCHA, hCaptcha, Turnstile, código por SMS ou app, certificado digital → caminho D para o login.
- Elementos e URLs que mudam a cada visita, ou proteção anti-bot agressiva → caminho E, ou desistir e avisar.

## Ferramentas que ajudam

Existem projetos que geram um cliente de API a partir do tráfego gravado do navegador. Se o usuário já usa um, aproveite. A skill não depende de nenhum deles: o HAR e os scripts acima bastam.
