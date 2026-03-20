# ADR 010: Pipeline ETL para SQL

**Data:** 2025-03-01

**Status:** Aceite

**Responsável/Autores:** Gonçalo Alves e Pedro Teixeira

---

## 1. Contexto e Problema

O sistema requer uma pipeline ETL (Extract, Transform, Load) para processar e armazenar dados estruturados relativos ao mercado de skins.

Esta pipeline deve:
- Integrar com a estratégia de ingestão definida (ADR 004);
- Garantir qualidade e consistência dos dados;
- Alimentar a base de dados SQL (PostgreSQL);
- Suportar queries analíticas para o dashboard.

É necessário escolher uma abordagem que facilite o desenvolvimento, manutenção e integração com o ecossistema Python.

---

## 2. Opções Consideradas

* Opção 1 - Utilizar ORM SQLAlchemy
* Opção 2 - Utilizar ORM Tortoise

---

## 3. Decisão

**SQLAlchemy**

---

## 4. Justificação

A escolha de SQLAlchemy permite implementar de forma eficiente a componente de carregamento (Load) da pipeline ETL, mantendo uma arquitetura simples e robusta.

### Papel no ETL:

- **Extract**: Dados obtidos via APIs, scraping e datasets (ADR 004);
- **Transform**: Limpeza, normalização e preparação dos dados;
- **Load**: Inserção estruturada na base de dados PostgreSQL via SQLAlchemy.

### Vantagens:
- Biblioteca madura e amplamente utilizada;
- Boa integração com PostgreSQL;
- Flexibilidade para queries complexas;
- Compatibilidade com arquitetura existente (FastAPI, Docker);
- Facilita manutenção e evolução do sistema.

### Comparação com alternativas:
- **Tortoise ORM**: Alternativa válida, mas menos madura e com menor adoção na comunidade.

SQLAlchemy oferece maior estabilidade e flexibilidade para suportar o pipeline ETL e as necessidades analíticas do sistema.

---

## 5. Consequências

### Positivas
- Estrutura clara e modular do pipeline ETL;
- Integração eficiente com PostgreSQL;
- Facilidade de manutenção e evolução;
- Suporte a queries analíticas complexas;
- Boa integração com o restante sistema.

### Negativas
- Necessidade de definir modelos e schemas explicitamente;
- Curva de aprendizagem inicial;
- Possível overhead comparado com queries SQL diretas.

### Mitigações
- Uso de boas práticas na definição de modelos;
- Separação clara das fases do ETL;
- Otimização de queries quando necessário;
- Monitorização de performance.