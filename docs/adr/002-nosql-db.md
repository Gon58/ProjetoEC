# ADR 002: Base de Dados Não Relacional (NoSQL)

**Data:** 2025-02-17

**Status:** Aceite

**Responsável/Autores:** Fernando Pires, João Costa

## 1. Contexto e Problema

Para armazenar informação menos estruturada como *posts* em websites como o Reddit, comentários de utilizadores, notícias e *logs* de utilização, uma base de dados NoSQL é a melhor escolha.

## 2. Opções Consideradas

* Opção 1 - Document Store - MongoDB
* Opção 2 - Key-Value - Redis

## 3. Decisão

**MongoDB**.

## 4. Justificação

**MongoDB** foi escolhido pela familiaridade com a ferramenta, e porque os tipos de base de dados *document store* se enquadram melhor nos casos de uso do projeto. Algum outro paradigma como *key-value* foi descartado devido à melhor adequação do anterior.
