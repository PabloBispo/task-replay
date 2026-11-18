"""
Exemplo completo do caminho B contra um site de treino público (quotes.toscrape.com).

Tarefa: fazer login (formulário com token CSRF) e exportar para CSV as citações
das tags listadas em entrada.csv. Roda sem navegador e sem gastar token.

    pip install httpx beautifulsoup4
    python executar.py --teste entrada.csv
    python executar.py entrada.csv
"""
import argparse
import csv
import random
import time

import httpx
from bs4 import BeautifulSoup

BASE = "https://quotes.toscrape.com"


def campos_ocultos(html):
    soup = BeautifulSoup(html, "html.parser")
    return {i["name"]: i.get("value", "")
            for i in soup.select("input[type=hidden]") if i.get("name")}


def login(client):
    # Passo 1: GET /login devolve o csrf_token num input oculto
    r = client.get("/login")
    # Passo 2: POST /login com usuário, senha e o token (o site de treino aceita qualquer usuário)
    dados = campos_ocultos(r.text) | {"username": "teste", "password": "teste"}
    r = client.post("/login", data=dados)
    if "Logout" not in r.text:
        raise SystemExit("Login falhou.")
    print("Login ok.")


def citacoes_da_tag(client, tag):
    # Passo 3: GET /tag/{tag}/page/{n}/ até não haver botão "Next"
    pagina, saida = 1, []
    while True:
        soup = BeautifulSoup(client.get(f"/tag/{tag}/page/{pagina}/").text, "html.parser")
        for q in soup.select(".quote"):
            saida.append({
                "tag": tag,
                "autor": q.select_one(".author").get_text(strip=True),
                "texto": q.select_one(".text").get_text(strip=True).strip("“”"),
            })
        if not soup.select_one("li.next"):
            return saida
        pagina += 1
        time.sleep(random.uniform(0.5, 1.5))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("--teste", action="store_true", help="mostra o que seria salvo e para")
    args = ap.parse_args()
    tags = [linha["tag"] for linha in csv.DictReader(open(args.entrada, encoding="utf-8-sig"))]

    with httpx.Client(base_url=BASE, follow_redirects=True, timeout=30) as client:
        login(client)
        todas = []
        for tag in tags:
            itens = citacoes_da_tag(client, tag)
            print(f"{tag}: {len(itens)} citações")
            todas += itens

    if args.teste:
        print("\nModo teste. Primeiras linhas que seriam salvas:")
        for i in todas[:3]:
            print(" ", i)
        return
    # Passo 4 (CONFIRMAR): gravar o arquivo de saída
    if input(f"\nSalvar {len(todas)} citações em resultado.csv? [s/N] ").strip().lower() != "s":
        return
    with open("resultado.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["tag", "autor", "texto"])
        w.writeheader()
        w.writerows(todas)
    print("Salvo em resultado.csv.")


if __name__ == "__main__":
    main()
