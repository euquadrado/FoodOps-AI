# Arquitetura e decisões

O Streamlit envia HTTP ao FastAPI. Somente o backend conhece o banco. A sessão
SQLAlchemy dura uma requisição; os contratos Pydantic validam entradas e saídas.
Falhas do banco retornam 503 sem expor SQL ou credenciais. No PostgreSQL, a API
inicia transações com `SET TRANSACTION READ ONLY`; o seed usa uma sessão separada.

Order possui relações com pagamentos e eventos. Valores são Numeric(10,2); chaves
estrangeiras e status são indexados. Eventos têm ordenação por data e ID.
O seed insere IDs ausentes numa transação, sem modificar registros existentes.
Ele não é mecanismo de migração nem deve ser executado concorrentemente.

DEMO executa diagnóstico por regras. AI usa Responses API, schemas estritos,
allowlist de funções, validação de argumentos, escopo por pedido e limite de chamadas.
O SDK recebe timeout e nenhum retry automático. Resultados de ferramentas são JSON
real do banco, nunca exemplos fingindo consultas no prompt.

O diagnóstico principal preserva regras e evidências. Não se infere estorno pelo
cancelamento nem causa do atraso apenas pelo status. A explicação livre do modelo
é complementar, identificada e passível de erros. A lista de hipóteses das regras
fica vazia atualmente, evitando apresentar suposições como fatos.

Campos textuais são dados não confiáveis. Não influenciam regras nem liberam SQL,
comandos ou alterações financeiras. Prompt injection na explicação do LLM continua
sendo limitação, assim como ausência de autenticação. O MVP é de uso local.

Compose mantém volume PostgreSQL, aguarda healthchecks e popula o banco antes da API.
A imagem executa com usuário sem privilégios; backend e frontend usam a mesma imagem
para reduzir configuração. As portas são publicadas em localhost.

Testes usam SQLite rápido ou PostgreSQL exclusivo. O CI usa PostgreSQL. Mocks validam
o protocolo OpenAI sem custos, mas não avaliam a qualidade de um modelo real.
