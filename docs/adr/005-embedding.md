# ADR 005: Modelo de Embedding para Vetorização

**Data:** 2026-03-01

**Status:** Aceite

**Responsável/Autores:** André Carvalho, João Costa

---

## 1. Contexto e Problema

O sistema RAG requer a conversão de dados não estruturados em embeddings vetoriais para permitir:
- Pesquisa semântica;
- Suporte à decisão baseado em contexto;
- Recuperação eficiente de informação.

De acordo com os requisitos do sistema, é necessário garantir:
- Tempo de resposta aceitável (< 10s);
- Baixo custo (contexto académico);
- Integração com arquitetura local (Docker);
- Qualidade semântica suficiente para RAG.

---

## 2. Opções Consideradas

* Opção 1 - Ollama com `embeddinggemma` (local)
* Opção 2 - Sentence-Transformers `all-MiniLM-L6-v2` (local)
* Opção 3 - Ollama com `nomic-embed-text` (local)
* Opção 4 - Cohere Embed API (cloud)

---

## 3. Decisão

**Ollama com modelo `embeddinggemma` (local)**

---

## 4. Justificação

A escolha recai sobre um modelo local devido ao melhor controlo sobre custo, latência e privacidade.

### Vantagens:
- Execução local (sem dependência de APIs externas);
- Sem custos e sem rate limits;
- Boa qualidade semântica (768 dimensões);
- Latência adequada ao sistema (< 10s global);
- Integração direta com Docker e restante arquitetura;
- Facilidade de substituição de modelo no ecossistema Ollama.

### Comparação com alternativas:
- **Sentence-Transformers**: Simples e leve, mas com menor qualidade semântica comparativamente;
- **nomic-embed-text**: Alternativa válida, mas sem vantagens claras face à opção escolhida;
- **Cohere API**: Boa qualidade, mas introduz custos, dependência externa e latência adicional.

A decisão privilegia uma solução local e estável, adequada ao contexto de MVP.

---

## 5. Consequências

### Positivas
- Independência de serviços externos;
- Redução de custos (zero uso de APIs pagas);
- Maior controlo sobre latência e desempenho;
- Boa integração com pipeline RAG;
- Alinhamento com arquitetura containerizada.

### Negativas
- Maior consumo de recursos (RAM/CPU);
- Necessidade de gerir um serviço adicional (Ollama);
- Possível limitação na qualidade face a modelos cloud mais avançados.

### Mitigações
- Monitorização de performance e latência;
- Possibilidade de troca de modelo dentro do ecossistema Ollama;
- Escalar para solução cloud caso necessário em fases futuras;
- Limitar volume de embeddings no MVP.