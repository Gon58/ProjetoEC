# ADR 012: Pipeline ETL para SQL

**Data:** 2025-03-01

**Status:** Aceite

**Responsável/Autores:** Gonçalo Alves

## 1. Contexto e Problema

De modo a armazenar e tratar os dados recolhidos relativos aos preços das skins, surge a necessidade de implementar uma pipeline ETL para carregar os dados para a base de dados PostgreSQL. 

## 2. Opções Consideradas

* Opção 1 - Utilizar a ORM SQLAlchemy
* Opção 2 - Utilizar a Tortoise ORM

## 3. Decisão

**SQLAlchemy**.

## 4. Justificação

**SQLAlchemy** foi escolhida, visto que é a ORM PostgreSQL mais popular do python e, comparativamente à Tortoise ORM, apresenta uma documentação mais extensa, é mais simples, mais robusta e mais estável em ambientes de produção

Assim, a SQLAlchemy permite manter uma arquitetura simples, estável e de fácil manutenção e é a mais adequada aos requisitos do projeto.