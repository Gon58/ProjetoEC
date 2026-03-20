# ADR 004: Estratégia de Ingestão e Atualização de Dados (Frequência)

**Data:** 2026-02-24

**Status:** Proposto

**Responsável/Autores:** André Carvalho, João Costa

---

## 1. Contexto e Problema

O projeto foca-se na economia de *skins* de CS:GO, um mercado altamente volátil com milhares de transações por hora.

É necessário definir uma estratégia de ingestão de dados que permita:
- Cumprir o requisito de >100k registos;
- Garantir dados suficientemente atualizados para análise;
- Integrar com o pipeline ETL;
- Minimizar complexidade de implementação (MVP).

A dúvida principal é se devemos optar por ingestão em tempo real ou em batch.

---

## 2. Opções Consideradas

* **Opção 1:** Extração em Tempo Real (*Streaming* / *Websockets*)
* **Opção 2:** *Pull* periódico em *batch* (com dataset histórico)
* **Opção 3:** *Pull* manual apenas no arranque do sistema

---

## 3. Decisão

**Opção 2: Pull diário em batch, complementado com dataset histórico**

---

## 4. Justificação

A escolha de uma estratégia *batch* está alinhada com a abordagem MVP recomendada para o projeto.

### Vantagens:
- Permite atingir rapidamente o requisito de >100k registos (via dataset histórico);
- Reduz significativamente a complexidade de implementação;
- Evita problemas de *rate limiting* nas APIs;
- Facilita integração com pipeline ETL (processamento periódico);
- Garante dados suficientemente atualizados para análise de tendências.

### Frequência definida:
- **Execução diária (1x/dia, durante madrugada — ex: 03:00)**
- Minimiza impacto de carga e permite processamento offline

### Comparação com alternativas:
- **Tempo real**: Maior complexidade (infraestrutura, sincronização, escalabilidade), desnecessário para MVP;
- **Manual**: Não garante atualização contínua nem consistência dos dados.

---

## 5. Consequências

### Positivas
- Implementação simples e robusta;
- Cumprimento rápido dos requisitos de dados;
- Integração direta com pipeline ETL;
- Redução de risco técnico;
- Alinhamento com WBS (Semana 3 – Ingestão de Dados).

### Negativas
- Dados não estão em tempo real;
- Possível atraso na deteção de eventos recentes;
- Menor granularidade temporal.

### Mitigações
- Ajustar frequência para intervalos menores (ex: 6h ou 1h) se necessário;
- Complementar com análise histórica (menos dependente de tempo real);
- Evoluir para ingestão híbrida (batch + near real-time) numa fase futura.