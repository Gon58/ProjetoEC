# ADR 011: Estratégia de Health Check da API

**Data:** 2026-02-28

**Status:** Aceite

**Responsável/Autores:** Luís Figueiredo

## 1. Contexto e Problema

A API Backend precisa de expor um endpoint /health para monitorização e orquestração (ex: Docker Compose). O desafio é decidir a abordagem para validar o estado das dependências (PostgreSQL, MongoDB e ChromaDB), equilibrando a precisão do diagnóstico do sistema com a carga gerada nas bases de dados por verificações constantes de conectividade num contexto de MVP.

## 2. Opções Consideradas

* Opção 1 - Verificação síncrona a cada request (On-Demand)
* Opção 2 - Verificação periódica em background com Cache
* Opção 3 - Apenas Liveness (sem verificar dependências)


## 3. Decisão

Opção 1 - Executar todas as verificações de conectividade a cada chamada ao `/health`

## 4. Justificação

A opção On-Demand foi escolhida por privilegiar a simplicidade de implementação e manutenção, adequando-se perfeitamente ao contexto de um MVP com tráfego limitado. Como o volume de requisições de health check será baixo e espaçado pelos orquestradores, a latência introduzida e a carga nas bases de dados são negligenciáveis. Esta abordagem garante um estado atualizado em tempo real, evitando a complexidade desnecessária de gerir concorrência ou cache de background tasks numa fase prematura do projeto.