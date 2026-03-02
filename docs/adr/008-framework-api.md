# ADR 008: Framework para a API Backend

**Data:** 2026-02-27

**Status:** Aceite

**Responsável/Autores:** Luís Figueiredo

## 1. Contexto e Problema

Para o desenvolvimento da API Backend, é necessário escolher um framework que permita uma implementação eficiente, escalável e de fácil manutenção. O framework deve ser compatível com as tecnologias utilizadas no projeto e deve oferecer suporte para as funcionalidades necessárias, como autenticação, roteamento, e integração com a base de dados.

## 2. Opções Consideradas

* Opção 1 - Flask
* Opção 2 - Django
* Opção 3 - FastAPI

## 3. Decisão

FastAPI

## 4. Justificação

O FastAPI foi selecionado pela sua alta performance e suporte nativo a operações assíncronas (async/await), o que será crítico na Fase 2 quando a API tiver de aguardar pelas respostas do modelo de linguagem (LLM) ou fazer queries simultâneas ao Postgres e MongoDB. Adicionalmente, gera documentação Swagger interativa de forma automática e é facilmente configurável no `docker-compose.yml` utilizando o servidor Uvicorn.
