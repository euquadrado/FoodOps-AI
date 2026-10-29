# FoodOps AI — Intelligent Order Diagnostics Agent

Agente de Inteligência Artificial Generativa desenvolvido com Python, FastAPI,
PostgreSQL e LLMs para investigação de falhas em operações simuladas de delivery.

Projeto de portfólio educacional, independente e sem vínculo oficial com o iFood.
Todos os dados são fictícios. O objetivo é cruzar pedidos, pagamentos e eventos para
explicar cancelamentos, recusas, atrasos e divergências com evidências consultáveis.

## Tecnologias e arquitetura

Python 3.11+, FastAPI, Pydantic 2, SQLAlchemy 2, PostgreSQL 16, SDK oficial OpenAI,
Streamlit, Pytest, Ruff, Docker e GitHub Actions. Sem frameworks de agentes ou RAG.

```mermaid
flowchart TD
    UI[Streamlit] --> API[FastAPI]
    API --> Agent[AgentService]
    Agent <--> LLM[OpenAI Responses API - AI MODE]
    Agent --> Tools[Ferramentas Python somente leitura]
    Tools --> Rules[Diagnóstico por regras]
    Tools --> DB[(PostgreSQL: orders / payments / order_events)]
```

O frontend acessa somente a API. A ORM realiza consultas parametrizadas. O modelo
escolhe entre `get_order_details`, `get_order_payment`, `get_order_events` e
`get_order_diagnosis`. O servidor valida os argumentos, consulta o banco e devolve
JSON por `function_call_output`; o modelo continua até a resposta final.
São permitidas oito chamadas de ferramentas e até nove solicitações ao modelo,
cada uma com timeout de 20 segundos e sem retries automáticos.

O diagnóstico principal é calculado pelas regras. A explicação livre do LLM aparece
separada e identificada como passível de erros. Uma resposta sem chamada bem-sucedida
de `get_order_diagnosis` é recusada. Dados nunca autorizam instruções ou comandos.

## Executar com Docker

Pré-requisitos: Git e Docker Desktop com containers Linux.

```powershell
git clone https://github.com/euquadrado/FoodOps-AI.git
cd FoodOps-AI
Copy-Item .env.example .env
docker compose up --build -d
```

- Interface: http://localhost:8501
- Swagger: http://localhost:8000/docs
- Saúde: http://localhost:8000/health
- PostgreSQL local: porta 5433; internamente a API usa `db:5432`.

O backend cria as tabelas e executa o seed antes de iniciar. O seed insere apenas IDs
ausentes, não remove nem atualiza dados. As credenciais de exemplo são para uso local.

```powershell
docker compose exec api python -m scripts.seed_database
docker compose ps
docker compose logs api
docker compose down
```

O volume do banco persiste após `down`. Todas as portas publicadas ficam em localhost.

## Executar sem Docker para a aplicação

Instale Python 3.11+ e PostgreSQL; pode usar `docker compose up -d db` apenas para o banco.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m scripts.seed_database
uvicorn app.main:app --reload
```

Em outro terminal, com o ambiente ativado: `streamlit run frontend/streamlit_app.py`.
Configure `DATABASE_URL` para seu banco. `API_URL` é variável de ambiente do frontend,
com padrão `http://localhost:8000` na execução local.

## Modos e configuração

| Variável | Uso |
|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Banco do Compose |
| `DATABASE_URL` | Conexão SQLAlchemy local; Compose compõe usando `POSTGRES_*` |
| `AGENT_MODE` | `demo` (padrão) ou `ai` |
| `OPENAI_API_KEY` | Chave privada, apenas no `.env` |
| `OPENAI_MODEL` | Modelo com function calling, padrão `gpt-4.1-mini` |
| `MAX_TOOL_CALLS` | Limite, padrão 8, configurável na execução local |
| `LLM_TIMEOUT` | Timeout por solicitação, padrão 20, configurável localmente |
| `API_URL` | Endereço da API para o frontend |

DEMO usa regras e PostgreSQL, sem LLM ou tokens. AI usa a OpenAI API real.
Para ativar, configure `AGENT_MODE=ai` e `OPENAI_API_KEY` no `.env` e execute:

```powershell
docker compose up -d --force-recreate api frontend
```

O modelo deve estar disponível à sua conta. Sem chave, o modo ativo continua DEMO.
Falhas do LLM retornam 503; não são disfarçadas como sucesso de IA.
Nunca coloque chaves no código, em prints ou no Git.

## Roteiro e exemplos

1. Abra o dashboard e veja os indicadores consultados do PostgreSQL.
2. Explore o pedido 1052, o pagamento e os eventos.
3. Pergunte: "Por que o pedido 1052 foi cancelado?"
4. Compare com "O que aconteceu com o pedido 1061?", cuja causa não está registrada.
5. Confira modo, ferramentas, evidências e tempo de execução.

Outras perguntas: "Por que o pagamento do pedido 1053 foi recusado?",
"O pedido 1056 está atrasado?", "Há divergência no pedido 1060?" e
"O que aconteceu com o pedido 9999?". Cada pergunta deve conter um único ID;
não há memória de contexto no backend e números adicionais tornam a pergunta ambígua.

### Cenários determinísticos

| ID | Situação e conclusão |
|---|---|
| 1052 | Timeout de confirmação, cancelamento e pagamento aprovado; estorno não comprovado |
| 1053 | Pagamento recusado; motivo bancário não detalhado |
| 1054 | Entregue, sem falha registrada |
| 1055 | Aguardando confirmação; causa de problema não determinada |
| 1056 | Atraso registrado, sem causa detalhada |
| 1057 | Falha técnica no processamento |
| 1058 | Cancelamento pelo cliente e pagamento estornado |
| 1059 | Falha de comunicação com restaurante |
| 1060 | Valor aprovado diverge do pedido |
| 1061 | Cancelado sem motivo registrado; evidência insuficiente |

Os dez cenários se repetem até 1151, totalizando 100 pedidos. Datas fixas em janeiro
de 2026 tornam os resultados reproduzíveis; não representam atividade em tempo real.

## API

`GET /health`, `GET /metrics`, `GET /orders?offset=0&limit=20`, `GET /orders/{id}`,
`GET /orders/{id}/events`, `GET /orders/{id}/payments` e `POST /agent/diagnose`.
Os contratos completos estão em `/docs`.

```powershell
Invoke-RestMethod http://localhost:8000/agent/diagnose -Method Post `
  -ContentType 'application/json; charset=utf-8' `
  -Body '{"message":"Por que o pedido 1052 foi cancelado?"}'
```

A resposta inclui resumo, problema, diagnóstico, evidências, hipóteses, recomendação,
modo, ferramentas e tempo. 404 indica pedido ausente; 422, entrada inválida; 503,
indisponibilidade do banco ou da IA.

## Estrutura

```text
app/                 Configuração, ORM, contratos e endpoints
  services/          Regras de diagnóstico e ciclo do agente
  tools/             Ferramentas de leitura e validação
frontend/            Dashboard, explorador e assistente
scripts/             Criação inicial de tabelas e seed
tests/               Testes de comportamento, API e mocks OpenAI
docs/                Decisões de arquitetura
.github/workflows/   CI com PostgreSQL e Ruff
```

## Testes

```powershell
pytest -q
ruff check .
ruff format --check .
```

Por padrão os testes usam SQLite em memória. Para executar contra PostgreSQL,
crie um banco **descartável exclusivo** e configure `TEST_DATABASE_URL`:

```powershell
$env:TEST_DATABASE_URL='postgresql+psycopg://foodops:local_demo_only@localhost:5433/foodops_test'
pytest -q
```

Os fixtures criam e removem tabelas; nunca use o banco da demonstração nessa variável.
O CI já cria PostgreSQL isolado. `docker compose exec api pytest -q` executa a suíte
rápida sem instalar Python no host. Chamadas OpenAI são mockadas e não geram custos.

## Decisões, limitações e melhorias

- Arquitetura síncrona simples e valores monetários Decimal/Numeric.
- Ferramentas sem escrita, SQL livre ou execução de comandos, restritas ao pedido solicitado.
- Descrições de eventos não controlam as regras. A explicação livre do LLM pode errar
  ou sofrer prompt injection; confira as evidências.
- Sem autenticação, rate limiting ou autorização por usuário: uso local educacional.
- Usuário SQL também inicializa o seed; a API usa transações somente leitura. Separar
  credenciais de seed/consulta é melhoria futura.
- `create_all` atende o esquema inicial; alterações futuras precisam de migrações.
- Dependências usam faixas compatíveis; lockfile é melhoria para reprodução exata.
- AI requer chave, saldo e acesso ao modelo. Testes com mocks não validam qualidade real.
- Próximas melhorias: Alembic, credencial SQL somente leitura, autenticação, rate limiting,
  avaliações de fidelidade e telemetria. RAG e embeddings ficam fora deste MVP.

## Screenshots

Área reservada para capturas do dashboard, explorador e assistente.

## Publicação

Trabalhe na branch `feature/foodops-ai-mvp`, execute os checks, revise `git diff`,
crie o commit e envie com `git push -u origin feature/foodops-ai-mvp`. Abra um Pull
Request para `main`, sem merge automático. Nunca adicione `.env` ou credenciais.

Integração baseada na [documentação oficial de function calling](https://developers.openai.com/api/docs/guides/function-calling).
