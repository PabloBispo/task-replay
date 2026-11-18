"""
Mapa de Execução · modelo dos caminhos C e D (Playwright, com login assistido).

Uso:
    python executar.py --teste entrada.csv
    python executar.py entrada.csv

Se não houver sessão salva (ou ela expirou), abre o navegador visível para você
fazer o login, resolver captcha ou 2FA. Depois segue sozinho em modo headless.
"""
import argparse
import csv
import os
import random
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import Page, expect, sync_playwright

load_dotenv()
BASE = os.environ["SISTEMA_URL"].rstrip("/")
SESSAO = Path("sessao/estado.json")
RESULTADO = Path("resultado.csv")


def logado(page: Page) -> bool:
    # TODO: algo que só aparece para quem está logado
    return page.get_by_text("Sair").count() > 0


def login_assistido(p) -> None:
    SESSAO.parent.mkdir(exist_ok=True)
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context()
    page = ctx.new_page()
    page.goto(f"{BASE}/login")                                  # TODO
    input("Faça o login no navegador (captcha, 2FA, certificado). Depois aperte Enter aqui. ")
    ctx.storage_state(path=str(SESSAO))
    browser.close()
    print("Sessão salva.")


def preparar(page: Page, item: dict) -> dict:
    """Preenche tudo até antes do botão com consequência."""
    page.goto(f"{BASE}/formulario")                             # TODO
    if not logado(page):
        raise PermissionError("sessão expirada")
    # TODO: um passo por linha, seletores por rótulo ou papel
    page.get_by_label("Campo exemplo").fill(item["coluna_exemplo"])
    return {"campo_exemplo": item["coluna_exemplo"]}


def confirmar(page: Page) -> str:
    page.get_by_role("button", name="Enviar").click()           # TODO
    expect(page.get_by_text("Enviado com sucesso")).to_be_visible(timeout=30_000)
    return page.locator(".protocolo").inner_text()              # TODO


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("--teste", action="store_true")
    ap.add_argument("--sim", action="store_true")
    ap.add_argument("--ver", action="store_true", help="mostra o navegador")
    args = ap.parse_args()
    itens = list(csv.DictReader(open(args.entrada, encoding="utf-8-sig")))

    with sync_playwright() as p:
        if not SESSAO.exists():
            login_assistido(p)
        browser = p.chromium.launch(headless=not args.ver)
        ctx = browser.new_context(storage_state=str(SESSAO))
        page = ctx.new_page()
        novo = not RESULTADO.exists()
        with RESULTADO.open("a", newline="", encoding="utf-8") as f:
            out = csv.writer(f)
            if novo:
                out.writerow(["item", "status", "resultado"])
            for n, item in enumerate(itens, 1):
                try:
                    dados = preparar(page, item)
                    print(f"\n[{n}/{len(itens)}] vai enviar: {dados}")
                    if args.teste:
                        out.writerow([n, "teste", ""])
                        continue
                    if not args.sim and input("Confirmar? [s/N] ").strip().lower() != "s":
                        out.writerow([n, "pulado", ""])
                        continue
                    res = confirmar(page)
                    print(f"   ok: {res}")
                    out.writerow([n, "ok", res])
                except PermissionError:
                    SESSAO.unlink(missing_ok=True)
                    sys.exit("Sessão expirada. Rode de novo para fazer o login assistido.")
                except Exception as e:
                    print(f"   erro: {e}")
                    out.writerow([n, "erro", str(e)[:200]])
                time.sleep(random.uniform(1, 3))
        browser.close()


if __name__ == "__main__":
    main()
