# Validação do MVP — 29/10/2026

Ambiente: Docker Desktop, containers Linux e Python 3.12.

- `pytest -q` via container com volume do código: **44 passed** usando SQLite em memória.
- A mesma suíte com `TEST_DATABASE_URL` apontando para PostgreSQL 16 exclusivo:
  **44 passed**. Nenhuma chamada real à OpenAI.
- `ruff check .`: aprovado.
- `ruff format --check .`: 19 arquivos Python formatados.
- `docker compose up --build -d`: build e inicialização concluídos.
- PostgreSQL, API e frontend: healthchecks saudáveis.
- Seed executado novamente: **0 pedidos inseridos**, preservando os 100 existentes.
- `SHOW transaction_read_only` na sessão da API atualizada: **on**.
- Navegador: dashboard exibiu 100 pedidos, 10 entregues, 40 cancelados e 10 recusas.
- Chat consultou o pedido 1052 e exibiu timeout, pagamento aprovado, evidências e
  recomendação de verificar estorno sem afirmar reembolso.
- Teste Streamlit AppTest exercitou dashboard, explorador e chat com HTTP mockado.

Há um aviso de depreciação do TestClient Starlette sobre seu transporte httpx;
não houve falhas na suíte final. O teste de interface inicialmente teve caminho
relativo incorreto, corrigido antes das execuções finais.

AI MODE possui integração real de function calling implementada, validada com mocks.
**Não foi realizada chamada paga a um modelo real**, pois não foi configurada chave
nesta entrega. A fidelidade da explicação livre deve ser avaliada com a conta e o
modelo escolhidos pelo usuário. O CI foi configurado; seu resultado remoto deve ser
conferido no Pull Request.
