# ADR 003: Base de Dados Vetorial

**Data:** 2025-02-17

**Status:** Aceite

**Responsável/Autores:** Fernando Pires, João Costa

---

## 1. Contexto e Problema

O sistema requer a implementação de um mecanismo de Retrieval-Augmented Generation (RAG), conforme os requisitos técnicos do projeto.

Para isso, é necessário:
- Converter dados não estruturados em embeddings vetoriais;
- Armazenar esses embeddings;
- Realizar pesquisas por similaridade semântica (vector search).

Bases de dados tradicionais (SQL e NoSQL) não são adequadas para este tipo de operação, uma vez que não suportam eficientemente pesquisas por proximidade vetorial.

---

## 2. Opções Consideradas

* Opção 1 - Pinecone (serviço gerido, cloud)
* Opção 2 - Milvus (open source, distribuído)
* Opção 3 - Weaviate (open source com features avançadas)
* Opção 4 - Chroma (open source, leve, focado em integração local)

---

## 3. Decisão

**Chroma**

---

## 4. Justificação

**Chroma** foi escolhido por se adequar ao contexto de MVP e ao ambiente técnico do projeto.

### Vantagens:
- Simples de configurar e integrar com Python;
- Suporte nativo a embeddings e vector search;
- Open source (sem custos);
- Integração fácil com Docker;
- Baixa complexidade operacional (ideal para protótipo funcional até semana 8).

### Comparação com alternativas:
- **Pinecone**: Solução robusta e escalável, mas dependente de cloud, custos e API keys (não ideal para MVP académico).
- **Milvus**: Muito potente e escalável, mas complexo de configurar e manter para o contexto do projeto.
- **Weaviate**: Oferece funcionalidades avançadas (ex: hybrid search), mas introduz complexidade adicional desnecessária nesta fase.

A escolha de Chroma permite cumprir o requisito de RAG com menor overhead e maior rapidez de desenvolvimento.

---

## 5. Consequências

### Positivas
- Implementação rápida do sistema RAG (alinhado com WBS semana 5);
- Baixa complexidade de setup;
- Integração direta com pipeline de embeddings;
- Independência de serviços externos (funciona localmente);
- Redução de custos e dependências externas.

### Negativas
- Menor escalabilidade comparado com soluções distribuídas;
- Menos funcionalidades avançadas (ex: hybrid search, clustering);
- Não otimizado para produção de grande escala.

### Mitigações
- Manter arquitetura modular (possibilidade de trocar por Milvus/Pinecone no futuro);
- Limitar escopo ao MVP;
- Monitorizar performance das queries;
- Avaliar upgrade para solução distribuída caso necessário.