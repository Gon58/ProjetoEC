# ADR 012: Seleção do Modelo LLM (llama3.1)

**Data:** 2026-03-21

**Status:** Aceite

**Responsável/Autores:** João Costa

---

## 1. Contexto e Problema

O sistema NeSy precisa de um modelo de linguagem para:

- interpretar perguntas do utilizador;
- decidir entre tool SQL e tool de pesquisa vetorial;
- gerar resposta final com base nos resultados das tools.

Era necessário escolher um modelo que funcionasse de forma estável em Docker, com boa qualidade em PT-PT e com custo operacional compatível com o MVP.

---

## 2. Opções Consideradas

- Opção 1 - `llama3.1`
- Opção 2 - `mistral`
- Opção 3 - `qwen2.5`

---

## 3. Decisão

Foi escolhido o modelo `llama3.1` como modelo LLM principal do backend.

---

## 4. Justificação

`llama3.1` foi escolhido por apresentar um bom equilíbrio entre:

- capacidade de seguir instruções de routing e uso de tools;
- qualidade de resposta para perguntas factuais e analíticas;
- disponibilidade e integração simples via Ollama no ambiente Docker;
- tempo de resposta aceitável para a fase MVP.

Trade-offs:

- pode exigir mais recursos que modelos mais leves;
- qualidade depende da versão/model card disponível no host Ollama.

---

## 5. Consequências

### Positivas

- Modelo único e explícito para toda a equipa.
- Menor ambiguidade em testes e demos.
- Configuração consistente no backend (`LLM_MODEL=llama3.1`).

### Negativas

- Dependência de um modelo específico no runtime.
- Eventual custo de latência/recursos em máquinas mais fracas.

### Mitigações

- Permitir override por variável de ambiente (`LLM_MODEL`).
- Reavaliar periodicamente com benchmark simples (qualidade, latência, robustez de tool-calling).
