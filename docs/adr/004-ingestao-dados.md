# ADR 004: Estratégia de Ingestão e Atualização de Dados (Frequência)

**Data:** 2026-02-24

**Status:** Proposto

**Responsável/Autores:** André Carvalho, João Costa

## 1. Contexto e Problema

O nosso projeto foca-se na economia de *skins* de CS:GO. O mercado é altamente volátil e ocorrem milhares de transações por hora. Surgiu a dúvida na equipa sobre a frequência ideal para extrair dados das APIs (ex: Skinport, Reddit): "Devemos fazer extrações em tempo real (a cada transação/nova *listing*) ou de forma periódica?"

## 2. Opções Consideradas

* **Opção 1:** Extração em Tempo Real (*Streaming* / *Websockets*).
* **Opção 2:** *Pull* diário em *batch* (fora de horas de ponta) complementado por um *dataset* histórico estático.
* **Opção 3:** *Pull* manual apenas quando o sistema é iniciado.

## 3. Decisão

Opção 2: *Pull* diário em *batch*.

## 4. Justificação

A adoção de uma estratégia MVP (Minimum Viable Product) é altamente recomendada devido ao tempo limitado de 15 semanas. Tentar implementar um sistema de tempo real adicionaria uma complexidade enorme de infraestrutura e aumentaria drasticamente o risco de *rate limits* (bloqueios de IP) nas APIs gratuitas que vamos utilizar.
O *dataset* histórico do Kaggle garante o cumprimento imediato do requisito de >100k registos, enquanto o *pull* diário garante que o sistema de suporte à decisão tem dados atualizados suficientes para comparar tendências de curto prazo sem comprometer a estabilidade do *pipeline* até à semana 8.
