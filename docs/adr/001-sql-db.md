# ADR 001: Base de Dados Relacional (SQL)

**Data:** 2025-02-16

**Status:** Aceite

**Responsável/Autores:** Fernando Pires, João Costa

---

## 1. Contexto e Problema

O projeto requer o armazenamento de grandes volumes de dados estruturados (>100k registos), incluindo histórico de preços de skins, transações e métricas agregadas.

De acordo com os requisitos do sistema, é necessário suportar:
- Queries analíticas para o dashboard (ex: tendências, comparações temporais);
- Operações estruturadas (SQL) utilizadas pelo agente (NeSy);
- Integração com pipelines ETL para ingestão e transformação de dados.

Bases de dados não relacionais não são adequadas para este tipo de operações analíticas e transacionais.

---

## 2. Opções Consideradas

* Opção 1 - MySQL
* Opção 2 - PostgreSQL
* Opção 3 - Oracle Database

---

## 3. Decisão

**PostgreSQL**

---

## 4. Justificação

**PostgreSQL** foi escolhido por apresentar um excelente equilíbrio entre robustez, flexibilidade e suporte a workloads analíticos.

### Vantagens:
- Forte suporte a queries complexas (JOINs, agregações, window functions);
- Excelente integração com pipelines ETL (ex: SQLAlchemy);
- Boa performance para workloads analíticos (essenciais para o dashboard);
- Open source, sem custos de licenciamento;
- Compatível com ambiente Docker (facilita DevOps).

### Comparação com alternativas:
- **MySQL**: Embora seja uma solução válida, apresenta menor flexibilidade em queries analíticas avançadas e menor foco em workloads complexos.
- **Oracle Database**: Muito robusto e completo, mas desadequado ao contexto MVP devido a custos, complexidade e necessidade de licenciamento.

A escolha de PostgreSQL alinha-se com a necessidade de suportar tanto operações transacionais como analíticas no sistema de suporte à decisão.

---

## 5. Consequências

### Positivas
- Suporte robusto a queries analíticas para o dashboard;
- Boa integração com ETL e ferramentas Python;
- Escalabilidade suficiente para o contexto do projeto;
- Baixo custo (open source);
- Facilita integração com a componente NeSy (queries via tools).

### Negativas
- Maior complexidade comparado com soluções mais simples;
- Necessidade de otimização de queries em datasets grandes;
- Overhead na modelação inicial (schema design).

### Mitigações
- Uso de ORM (SQLAlchemy) para simplificar interação;
- Indexação adequada para melhorar performance;
- Limitação do escopo ao MVP para evitar overengineering;
- Monitorização de queries críticas (logs + tuning futuro).