# Task Replay · {nome da tarefa}

## Contexto

- Tarefa: {descrição em uma frase}
- Sistema: {URL}
- Frequência: {ex.: 20 notas por mês}
- Login: {usuário e senha | 2FA | captcha | certificado A1/A3}
- Entrada: {ex.: clientes.csv com nome, CNPJ, valor, descrição}
- Saída: {ex.: PDF da nota em saida/ e número em resultado.csv}
- Caminho escolhido: {A | B | C | D | E}, porque {motivo}
- Termos de uso: {verificado em DATA: permite | não menciona | proíbe}

## Requisições (caminhos A a D)

| # | Método | URL | Envia | Recebe | Observação |
|---|---|---|---|---|---|
| 1 | GET | /login | | csrf_token (input oculto) | |
| 2 | POST | /login | usuário, senha, csrf_token | cookie de sessão | login assistido se houver captcha |
| 3 | ... | | | | |
| N | POST | /emitir | ... | número da nota | **CONFIRMAR** |

## Passos (caminho E, ou para leitura humana)

### Passo 1 · {nome}
- Tela:
- Elemento:
- Ação:
- Valor:
- Depois:
- Se der errado:

### Passo N · {nome} · CONFIRMAR
- Parar e mostrar ao usuário o que será enviado.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env    # preencha
python executar.py --teste entrada.csv   # roda até o CONFIRMAR
python executar.py entrada.csv
```

## Histórico de mudanças

- {DATA}: mapeamento inicial.
