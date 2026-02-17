# ADR 003: Base de Dados Vetorial

**Data:** 2025-02-17

**Status:** Aceite

**Responsável/Autores:** Fernando Pires, João Costa

## 1. Contexto e Problema

As outras bases de dados não se adequam para alimentar o sistema de *Retrieval-Augmented Generation* (RAG) no LLM, partindo de dados não estruturados a serem repartidos em *chunks*.

## 2. Opções Consideradas

* Opção 1 - Pinecone
* Opção 2 - Milvus
* Opção 3 - Weaviate
* Opção 4 - Chroma

## 3. Decisão

**Chroma**.

## 4. Justificação

**Chroma** foi escolhida por causa da estratégia *Minimum Viable Product* (MVP) exigir algo leve e simples (tempo limitado), sendo que esta também tem excelente integração com Python. Para além disso, tem imagem oficial no Docker, o que simplifica muito a configuração, e também é *open source*.

As outras opções, comparadamente, não ofereciam o produto mais adequado ao projeto a desenvolver.
