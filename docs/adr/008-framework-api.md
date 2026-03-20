# ADR 008: Framework para a API Backend

**Data:** 2026-02-27

**Status:** Aceite

**Responsável/Autores:** Luís Figueiredo

---

## 1. Contexto e Problema

Para o desenvolvimento da API Backend, é necessário escolher um framework que permita uma implementação eficiente, escalável e de fácil manutenção.

A API será responsável por:
- Expor endpoints para o sistema (chat, RAG, queries SQL);
- Orquestrar chamadas ao LLM e bases de dados (SQL, NoSQL, Vector DB);
- Integrar com o frontend (dashboard e chat).

O framework deve suportar:
- Operações assíncronas;
- Integração com Docker;
- Facilidade de testes e CI;
- Boa performance para múltiplas chamadas concorrentes.

---

## 2. Opções Consideradas

* Opção 1 - Flask
* Opção 2 - Django
* Opção 3 - FastAPI

---

## 3. Decisão

**FastAPI**

---

## 4. Justificação

O FastAPI foi escolhido por oferecer o melhor equilíbrio entre performance, simplicidade e suporte a funcionalidades modernas.

### Vantagens:
- Suporte nativo a async/await (crítico para chamadas ao LLM e múltiplas bases de dados);
- Alta performance comparável a frameworks mais complexos;
- Geração automática de documentação (Swagger/OpenAPI);
- Fácil integração com Docker (Uvicorn + containers);
- Boa integração com pipelines de CI (testes e validação automática);
- Simplicidade de desenvolvimento (menor overhead que Django).

### Comparação com alternativas:
- **Flask**: Mais simples, mas sem suporte nativo robusto a async e menos estruturado para projetos maiores;
- **Django**: Muito completo, mas excessivo para o contexto do projeto (overhead desnecessário para MVP).

A escolha de FastAPI permite desenvolver uma API moderna, eficiente e alinhada com os requisitos do sistema.

---

## 5. Consequências

### Positivas
- Melhor performance e escalabilidade;
- Suporte eficiente a operações concorrentes;
- Integração direta com Docker;
- Facilidade de integração com CI/CD;
- Documentação automática da API.

### Negativas
- Curva de aprendizagem inicial (async/await);
- Necessidade de gerir corretamente concorrência;
- Menor maturidade comparado com Django em alguns cenários.

### Mitigações
- Uso de boas práticas async;
- Testes automatizados no pipeline CI;
- Limitar complexidade da API no MVP;
- Evoluir arquitetura conforme necessário.