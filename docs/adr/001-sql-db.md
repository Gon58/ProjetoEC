# ADR 001: Base de Dados Relacional (SQL)

**Data:** 2025-02-16

**Status:** Aceite

**Responsável/Autores:** Fernando Pires, João Costa

## 1. Contexto e Problema

Para armazenar informação mais estruturada como histórico de preços e com elevado número de transações, era necssário implementar uma base de dados de modelo relacional. Sendo transações algo frequente por causa da mudança de valores de items, modelos não relacionais não seriam a melhor escolha.

## 2. Opções Consideradas

* Opção 1 - MySQL
* Opção 2 - PostgreSQL
* Opção 3 - Oracle Database

## 3. Decisão

**PostgreSQL**.

## 4. Justificação

**PostgreSQL** foi escolhida pela familiaridade com a ferramenta, robustez para escalabilidade, lidando com grandes volumes de dados. Para além disso, o facto de ser *open source*.
A principal desvantagem de MySQL e a razão para não ser escolhida é o facto de não ter funcionalidades SQL muito avançadas, um fator potencialmente limitante. Oracle Database não foi escolhida por ser proprietária e carregar com ela um contrato bastante restritivo, apesar de funcionalidades avançadas estarem presentes.
