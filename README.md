# Projeto EC

## Descrição

Projeto em desenvolvimento.

## Autores

André Dias

Fernando Pires

Gonçalo Silva

João Costa

Luís Figueiredo

Pedro Teixeira

## Instruções de Uso

1. Duplicar o ficheiro .env.example e renomear a cópia para .env.
2. Substituir os valores falsos pelas credenciais reais no ficheiro .env.
3. Correr docker-compose up.

## LLM (Ollama + Mistral)

Para geração de respostas RAG com LLM, o projeto usa o modelo `mistral` no Ollama.

1. Iniciar o serviço Ollama: `docker compose up -d ec-project-ollama`
2. Fazer pull do modelo: `docker exec ec-project-ollama ollama pull mistral`
3. Confirmar modelos disponíveis: `docker exec ec-project-ollama ollama list`

Prompts RAG estão externalizados em ficheiros para facilitar manutenção e evitar lógica de prompt hardcoded no código:

- `backend/src/prompts/rag_system_prompt.txt`
- `backend/src/prompts/rag_user_prompt.txt`

Para ajustar comportamento/estilo, editar apenas estes ficheiros. O código em `backend/src/services/llm.py` apenas carrega os templates e injeta `{query}` e `{context}`.

A camada LLM está em `backend/src/services/llm.py` e já formata o contexto recuperado com `distance` por chunk.

Comportamento automático para reduzir fricção de uso:

- O serviço tenta verificar automaticamente se o Ollama está acessível.
- Se não estiver, tenta iniciar `ec-project-ollama` com Docker Compose.
- Se o modelo não existir, tenta fazer pull automaticamente.

Variáveis úteis:

- `OLLAMA_AUTOSTART=1` (default) ativa tentativa de start automático.
- `OLLAMA_DOCKER_SERVICE=ec-project-ollama` define o nome do serviço Docker Compose.
- `OLLAMA_START_TIMEOUT_SECONDS=30` define timeout de espera para o Ollama subir.

## Teste Rápido do RAG

Para testar retrieval + resposta LLM sem escrever comandos longos:

1. Com query default:
	`.venv\Scripts\python.exe backend\src\scripts\rag_smoke_test.py`
2. Com query personalizada:
	`.venv\Scripts\python.exe backend\src\scripts\rag_smoke_test.py --query "What are players unhappy about?"`
