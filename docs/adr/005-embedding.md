# ADR 005: Modelo de Embedding para Vetorização

**Data:** 2026-03-01

**Status:** Aceito

**Responsável/Autores:** André Carvalho, João Costa

## 1. Contexto e Problema

O sistema RAG com Chroma DB precisa de converter os dados de entrada em embeddings vetoriais para:

- Recomendações semânticas por preço e características;
- Suporte a decisão de investimentos;
- Exploração de tendências de mercado;
- Tempo resposta < 10s.

A escolha do modelo de embedding é crítica para o trade-off entre **latência, custo, privacidade, e qualidade semântica**.

## 2. Opções Consideradas

* **Opção 1:** Ollama com  `embeddinggemma` (local, offline).
* **Opção 2:** Sentence-Transformers `all-MiniLM-L6-v2` (local).
* **Opção 3:** Ollama com `nomic-embed-text` (local, offline).
* **Opção 4:** Cohere Embed API (cloud, balanço custo/qualidade).

## 3. Decisão

**Implementado:** Ollama com modelo `embeddinggemma` (local, containerizado com Docker)

## 4. Justificação

### Por que Ollama com `embeddinggemma`?

**Vantagens:**

- **Latência:** ~100-200ms por embedding, aceitável para o requisito < 10s.
- **Dimensões:** 768 dimensões, melhor qualidade semântica.
- **Privacidade:** 100% local, dados permanecem *on-premises*.
- **Containerização:** Integra perfeitamente com arquitetura Docker existente (postgres, mongo, chroma).
- **Sem dependências API:** Zero custo, sem rate limits, sem chaves de API.
- **Batch-friendly:** Suporta processamento em lote via `embed_texts()`.
- **Ecosystem:** Ollama permite trocar de modelo facilmente se necessário.
- **Auto-download:** Modelo é baixado automaticamente na primeira utilização.

**Trade-offs:**

- Requer mais memória RAM.
- Adiciona um serviço extra ao Docker Compose.

### Arquitetura Implementada

1. **Serviço Ollama:** Container `ec-project-ollama` na porta 11434.
2. **Embedding Service:** `src/services/embeddings.py` com funções `embed_text()` e `embed_texts()` (sempre usa embeddinggemma).
3. **Integração Chroma:** `src/db/connections.py` com `index_document()` e `search_documents()`.
4. **API Endpoints:** `/index` (POST) e `/search` (POST) no `src/main.py`.
5. **Testes:** `tests/test_vectorial.py` com unittest + mocks, smoke tests validados.

### Estratégia de Escalamento

1. **MVP:** Deployment com `embeddinggemma` já concluído.
2. **Monitorizar:** Medir latência real em produção, validar < 10s.
3. **Futuro:** Se precisar de melhor performance → avaliar outros modelos Ollama (mxbai-embed-large, etc).
