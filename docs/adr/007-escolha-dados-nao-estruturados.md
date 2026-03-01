# ADR [Número]: Escolha da Fonte de Dados Não Estruturados

**Data:** 2026-02-23

**Status:** Aceite

**Responsável/Autores:** Luís Figueiredo

## 1. Contexto e Problema

O projeto exige a recolha e o armazenamento de um grande volume de dados não estruturados em formato de texto. O objetivo destes dados é alimentar a componente de Inteligência Artificial do sistema, especificamente o pipeline de Retrieval-Augmented Generation (RAG). É necessário obter opiniões, contexto humano e o sentimento da comunidade sobre o mercado e a economia de skins do CS2, complementando a base de dados SQL que guarda apenas valores numéricos e históricos de preços. O desafio é encontrar uma fonte fiável, de acesso viável e com escala suficiente para atingir as metas de volume do grupo (>100.000 registos).

## 2. Opções Consideradas

* Opção 1 - Reddit API
* Opção 2 - Twitter/X API
* Opção 3 - Steam Reviews API

## 3. Decisão

Steam Reviews API

## 4. Justificação

A escolha recai sobre a Steam Reviews API pela fiabilidade e pela ausência de barreiras de autenticação. O principal trade-off é a dificuldade de obter informação específica para o mercado de skins. Para superar esta limitação, a estratégia será ter um volume maior de dados que posteriormente será filtrado dependendo do conteúdo. A opção do Reddit, embora rica em conteúdo relevante (devido à comunidade ativa de mercado de skins) não é viável devido às dificuldades em obter credenciais de acesso.
