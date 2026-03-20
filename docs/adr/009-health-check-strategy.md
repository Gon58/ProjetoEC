# ADR 009: Estratégia de Health Check da API

**Data:** 2026-02-28

**Status:** Aceite

**Responsável/Autores:** Luís Figueiredo

---

## 1. Contexto e Problema

A API Backend necessita de expor um endpoint `/health` para permitir:

- Monitorização do estado do sistema;
- Integração com Docker (health checks);
- Verificação de conectividade com dependências (PostgreSQL, MongoDB, ChromaDB).

É necessário definir uma estratégia que equilibre:
- Precisão do estado do sistema;
- Simplicidade de implementação;
- Impacto no desempenho.

---

## 2. Opções Consideradas

* Opção 1 - Verificação síncrona a cada request (On-Demand)
* Opção 2 - Verificação periódica em background com cache
* Opção 3 - Apenas Liveness (sem verificar dependências)

---

## 3. Decisão

**Opção 1 - Verificação on-demand a cada chamada ao `/health`**

---

## 4. Justificação

A abordagem on-demand foi escolhida por ser simples, fiável e adequada ao contexto de MVP.

### Vantagens:
- Implementação simples e direta;
- Estado atualizado em tempo real;
- Sem necessidade de gestão de tarefas em background;
- Baixo impacto no sistema (baixo volume de chamadas).

### Comparação com alternativas:
- **Background + cache**: Introduz complexidade desnecessária para o contexto atual;
- **Liveness apenas**: Não valida dependências críticas (bases de dados).

Esta decisão está alinhada com a filosofia MVP, privilegiando simplicidade e rapidez de desenvolvimento.

---

## 5. Consequências

### Positivas
- Simplicidade de implementação;
- Diagnóstico fiável do estado das dependências;
- Integração direta com Docker;
- Baixo overhead em ambiente de baixo tráfego.

### Negativas
- Aumento de latência no endpoint `/health`;
- Pequena carga adicional nas bases de dados;
- Não escalável para sistemas de alto tráfego.

### Mitigações
- Limitar frequência de chamadas ao endpoint;
- Evoluir para estratégia com cache em cenários de maior escala;
- Monitorizar impacto em produção.