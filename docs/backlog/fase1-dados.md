# Fase 1 - Dados e Infraestrutura

## Semana 2 - Setup

- [ ] Definir domínio do problema
- [ ] Criar repositório Git
- [ ] Definir estratégia de branch
- [ ] Configurar Docker (Dockerfile + docker-compose)
- [ ] Configurar CI (lint + testes)
- ADRs: ADR 008

---

## Semana 3 - Ingestão de Dados

- [ ] Implementar scraping Reddit
- [ ] Implementar scraping Steam Market
- [ ] Importar dataset histórico (>100k registos)
- [ ] Validar qualidade dos dados
- [ ] Garantir comunicação entre containers
- User Stories: US06, US09
- ADRs: ADR 004, ADR 007

---

## Semana 4 - Persistência

- [ ] Configurar PostgreSQL
- [ ] Configurar MongoDB
- [ ] Configurar Chroma DB
- [ ] Implementar pipeline ETL (Extract + Transform + Load)
- [ ] Testar ligação Python → DBs
- User Stories: US01, US05, US09
- ADRs: ADR 001, ADR 002, ADR 003, ADR 010