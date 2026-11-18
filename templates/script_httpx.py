"""
Mapa de Execução · modelo do caminho B (httpx + BeautifulSoup).

Uso:
    python executar.py --teste entrada.csv   # roda tudo até o passo CONFIRMAR, sem executá-lo
    python executar.py entrada.csv           # pede confirmação a cada item

Ajuste as funções marcadas com TODO a partir das requisições do mapa.md.
"""
import argparse
import csv
import json
import os
import random
import sys
import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
BASE = os.environ["SISTEMA_URL"].rstrip("/")          # ex.: https://sistema.exemplo.com.br
SESSAO = Path("sessao/estado.json")
RESULTADO = Path("resultado.csv")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
}


class SessaoExpirada(Exception):
    pass


def campos_ocultos(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    return {i["name"]: i.get("value", "")
            for i in soup.select("input[type=hidden]") if i.get("name")}


def eh_tela_de_login(resp: httpx.Response) -> bool:
    # TODO: ajuste para o sistema (URL de login ou texto do formulário)
    return "/login" in str(resp.url) or 'name="password"' in resp.text


def abrir_sessao() -> httpx.Client:
    client = httpx.Client(base_url=BASE, headers=HEADERS, follow_redirects=True, timeout=30)
    if SESSAO.exists():
        # sessão salva pelo login assistido (Playwright)
        for c in json.loads(SESSAO.read_text())["cookies"]:
            client.cookies.set(c["name"], c["value"], domain=c["domain"], path=c["path"])
        return client
    # login simples, sem captcha. Com captcha ou 2FA, use login_assistido.py.
    r = client.get("/login")                                   # TODO: URL do login
    dados = campos_ocultos(r.text) | {
        "username": os.environ["SISTEMA_USUARIO"],             # TODO: nomes dos campos
        "password": os.environ["SISTEMA_SENHA"],
    }
    r = client.post("/login", data=dados)
    if eh_tela_de_login(r):
        sys.exit("Login falhou. Confira usuário e senha no .env.")
    return client


def preparar(client: httpx.Client, item: dict) -> dict:
    """Tudo que vem antes do passo com consequência. Devolve o que seria enviado."""
    r = client.get("/formulario")                              # TODO
    if eh_tela_de_login(r):
        raise SessaoExpirada
    return campos_ocultos(r.text) | {
        # TODO: mapear colunas do CSV para os campos do formulário
        "campo_exemplo": item["coluna_exemplo"],
    }


def confirmar(client: httpx.Client, dados: dict) -> str:
    """O passo CONFIRMAR. Só roda com o ok do usuário."""
    r = client.post("/enviar", data=dados)                     # TODO
    if eh_tela_de_login(r):
        raise SessaoExpirada
    soup = BeautifulSoup(r.text, "html.parser")
    return soup.select_one(".protocolo").get_text(strip=True)  # TODO: onde está o resultado


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("--teste", action="store_true", help="para antes do passo CONFIRMAR")
    ap.add_argument("--sim", action="store_true", help="confirma todos os itens sem perguntar")
    args = ap.parse_args()

    itens = list(csv.DictReader(open(args.entrada, encoding="utf-8-sig")))
    client = abrir_sessao()
    novo = not RESULTADO.exists()
    with RESULTADO.open("a", newline="", encoding="utf-8") as f:
        out = csv.writer(f)
        if novo:
            out.writerow(["item", "status", "resultado"])
        for n, item in enumerate(itens, 1):
            try:
                dados = preparar(client, item)
                visivel = {k: v for k, v in dados.items() if not k.startswith("__")}
                print(f"\n[{n}/{len(itens)}] vai enviar: {visivel}")
                if args.teste:
                    out.writerow([n, "teste", ""])
                    continue
                if not args.sim and input("Confirmar? [s/N] ").strip().lower() != "s":
                    out.writerow([n, "pulado", ""])
                    continue
                res = confirmar(client, dados)
                print(f"   ok: {res}")
                out.writerow([n, "ok", res])
            except SessaoExpirada:
                sys.exit("Sessão expirada. Rode o login assistido de novo e continue deste item.")
            except Exception as e:  # registra e segue para o próximo
                print(f"   erro: {e}")
                out.writerow([n, "erro", str(e)[:200]])
            time.sleep(random.uniform(1, 3))


if __name__ == "__main__":
    main()
