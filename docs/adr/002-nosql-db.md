# ADR 002: Base de Dados Não Relacional (NoSQL)

**Data:** 2025-02-17

**Status:** Aceite

**Responsável/Autores:** Fernando Pires, João Costa

---

## 1. Contexto e Problema

O projeto requer o armazenamento de dados não estruturados e semi-estruturados, incluindo:
- Comentários de utilizadores;
- Reviews e opiniões;
- Notícias;
- Logs de utilização do sistema.

Estes dados apresentam:
- Estrutura variável;
- Campos opcionais;
- Possível aninhamento (nested documents);
- Evolução ao longo do tempo.

De acordo com os requisitos do sistema, é necessário suportar armazenamento flexível e consultas eficientes sobre documentos, nomeadamente para alimentar o sistema de RAG e análise contextual.

---

## 2. Opções Consideradas

* Opção 1 - Document Store - MongoDB
* Opção 2 - Key-Value Store - Redis

---

## 3. Decisão

**MongoDB**

---

## 4. Justificação

**MongoDB** foi escolhido por ser uma base de dados orientada a documentos, adequada para dados não estruturados e com schema flexível.

### Vantagens:
- Suporte a documentos JSON/BSON com estrutura dinâmica;
- Permite dados aninhados (nested), ideais para comentários e metadata;
- Flexibilidade de schema (não exige estrutura fixa);
- Suporte a queries sobre campos específicos dentro dos documentos;
- Boa integração com Python e pipelines de ingestão;
- Compatível com Docker (facilita integração no sistema).

### Comparação com alternativas:
- **Redis**: Sendo uma base de dados key-value, é otimizada para caching e acesso extremamente rápido, mas não é adequada para armazenamento e consulta de documentos complexos ou análise de texto.
  
MongoDB permite armazenar e consultar dados de forma mais rica e expressiva, sendo mais adequado ao contexto do projeto.

---

## 5. Consequências

### Positivas
- Flexibilidade para lidar com dados heterogéneos e em evolução;
- Suporte natural a documentos complexos e aninhados;
- Facilita ingestão de múltiplas fontes (APIs, crawlers);
- Integração direta com pipeline de RAG (dados não estruturados);
- Reduz necessidade de transformação rígida de dados.

### Negativas
- Menor consistência comparado com SQL (eventual consistency);
- Queries complexas podem ser menos eficientes que SQL;
- Possível duplicação de dados (denormalização);
- Requer cuidado no design dos documentos.

### Mitigações
- Definir estrutura base de documentos (mesmo sendo flexível);
- Indexação de campos críticos para melhorar performance;
- Limitar complexidade das queries;
- Separar claramente responsabilidades entre SQL (estruturado) e NoSQL (não estruturado).