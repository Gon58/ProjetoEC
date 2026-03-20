# ADR 011: Estratégia de Performance vs Precisão dos Modelos

**Data:** 2026-02-25

**Status:** Aceite

**Responsável/Autores:** André Carvalho, João Costa

---

## 1. Contexto e Problema

O sistema inclui um Assistente Inteligente integrado com um dashboard, sendo necessário garantir uma boa experiência de utilização.

É necessário definir o trade-off entre:
- Precisão dos modelos (modelos maiores e mais lentos);
- Latência de resposta (modelos mais leves e rápidos).

Este fator impacta diretamente a usabilidade do sistema.

---

## 2. Opções Consideradas

* Opção 1 - Priorizar precisão (modelos grandes, maior latência)
* Opção 2 - Priorizar performance (modelos mais rápidos, menor latência)

---

## 3. Decisão

**Priorizar performance (baixa latência)**

---

## 4. Justificação

O sistema é orientado à tomada de decisão em tempo real, com interação direta entre chat e dashboard.

### Vantagens:
- Melhor experiência de utilizador;
- Respostas mais rápidas e interativas;
- Maior fluidez no uso do sistema;
- Compatível com uso em contexto real (não apenas batch).

### Alternativa rejeitada:
- **Alta precisão**: Introduz latência elevada, prejudicando a usabilidade e interação.

A precisão é parcialmente garantida por:
- Queries determinísticas (SQL);
- RAG sobre dados relevantes;
- LLM focado em sumarização/interpretação.

---

## 5. Consequências

### Positivas
- Melhor UX (respostas rápidas);
- Sistema mais fluido e interativo;
- Redução de frustração do utilizador;
- Melhor integração com dashboard dinâmico.

### Negativas
- Possível perda de precisão em algumas respostas;
- Dependência de qualidade dos dados (RAG/SQL);
- Limitação na complexidade das respostas.

### Mitigações
- Uso de ferramentas determinísticas (SQL, cálculos);
- Ajuste de prompts;
- Possibilidade de trocar modelos futuramente;
- Avaliação contínua com script de testes (eval.py).