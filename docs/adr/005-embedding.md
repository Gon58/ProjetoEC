# ADR 004: Modelo de Embedding para Vetorização

**Data:** 2026-02-24

**Status:** Proposto

**Responsável/Autores:** André Carvalho, João Costa

## 1. Contexto e Problema

O sistema RAG com Chroma DB precisa de converter os dados de entrada em embeddings vetoriais para:

- Recomendações semânticas por preço e características;
- Suporte a decisão de investimentos;
- Exploração de tendências de mercado;
- Tempo resposta < 10s.

A escolha do modelo de embedding é crítica para o trade-off entre **latência, custo, privacidade, e qualidade semântica**.

## 2. Opções Consideradas

* **Opção 1:** OpenAI `text-embedding-3-small` (API).
* **Opção 2:** Sentence-Transformers `all-MiniLM-L6-v2` (local).
* **Opção 3:** Ollama com `nomic-embed-text` (local, offline).
* **Opção 4:** Cohere Embed API (cloud, balanço custo/qualidade).

## 3. Decisão

**Fase 1 (MVP):** Sentence-Transformers `all-MiniLM-L6-v2` (local, sem dependências externas)  
**Fase 2 (escalamento):** Avaliar posteriormente possível migração para `all-mpnet-base-v2` ou explorar Ollama mediante latencia

## 4. Justificação

### Por que `all-MiniLM-L6-v2`?

**Vantagens:**

- **Latência:** ~50-100ms por embedding.
- **Tamanho:** 384 dimensõesm gasta menos espaço comparado a outros modelos.
- **Privacidade:** 100% local, dados permanecem *on-premisses* .
- **Simplicidade:** Integra direto com Python.
- **Custo:** Zero, também não tem rate limits (*open-source*).
- **Batch-friendly:** Processa 1000 skins em ~1-2 segundos (não testado*).

**Trade-offs:**

- Menos preciso que modelos maiores (`all-mpnet`: 768 dims) - ~2-5% queda em *retrieval accuracy*.
- Não vai conseguir perceber as nuances do domínio devido ao menor número de dims .

### Estratégia

1. **Baseline:** Deploy com `all-MiniLM-L6-v2`, medir tempo real de resposta
2. **Monitorizar:** Se latência < 5s → aceitar MVP  
3. **Escalar:** Se latência > 5s:
   - Tentar PEFT/LoRA (fine-tuning leve)
   - Ou migrar para `all-mpnet-base-v2`
   - Último recurso: Ollama para controlo total
