# ADR 006: Padronização de Idioma dos Dados

**Data:** 2026-02-25

**Status:** Aceite

**Responsável/Autores:** André Carvalho, João Costa

---

## 1. Contexto e Problema

O sistema processa dados não estruturados provenientes de múltiplas fontes (ex: Steam, Reddit, APIs de mercado), sendo estes maioritariamente em Inglês.

É necessário definir uma estratégia de idioma para:
- Armazenamento dos dados (SQL, NoSQL e Vector DB);
- Processamento no pipeline RAG;
- Interação com o utilizador via Chat.

A decisão impacta diretamente:
- Performance do sistema;
- Complexidade do pipeline;
- Qualidade da análise semântica.

---

## 2. Opções Consideradas

* Opção 1 - Traduzir todos os dados para Português antes de armazenar
* Opção 2 - Manter todos os dados em Inglês no backend

---

## 3. Decisão

**Manter todos os dados padronizados em Inglês no backend**

---

## 4. Justificação

A escolha de manter os dados em Inglês permite simplificar significativamente o sistema e melhorar a performance global.

### Vantagens:
- Evita processamento adicional de tradução em >100k registos;
- Reduz custo computacional e complexidade do pipeline;
- Mantém consistência com fontes de dados originais;
- Melhor compatibilidade com modelos de embeddings e LLMs (treinados maioritariamente em Inglês);
- Simplifica pipeline RAG.

### Alternativa rejeitada:
- **Tradução para Português**: Introduz overhead significativo, aumenta latência e pode degradar qualidade semântica.

O chatbot atua como camada de abstração, permitindo interação em Português enquanto o backend opera em Inglês.

---

## 5. Consequências

### Positivas
- Pipeline mais simples e eficiente;
- Melhor performance global;
- Melhor qualidade nos embeddings e RAG;
- Redução de custo computacional.

### Negativas
- Necessidade de tradução dinâmica no chatbot;
- Possível perda de nuance na tradução em tempo real;
- Dependência de modelos capazes de lidar com múltiplos idiomas.

### Mitigações
- Utilizar prompts que suportem multi-linguagem;
- Traduzir apenas input/output do utilizador (não os dados);
- Ajustar prompts para garantir respostas naturais em Português.