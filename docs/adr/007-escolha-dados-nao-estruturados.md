# ADR 007: Escolha das Fontes de Dados Não Estruturados

**Data:** 2026-02-23

**Status:** Aceite

**Responsável/Autores:** Luís Figueiredo

---

## 1. Contexto e Problema

O sistema requer dados não estruturados (texto) para alimentar o pipeline de RAG e permitir:

- Análise de sentimento da comunidade;
- Contextualização de tendências de mercado;
- Suporte à decisão com base em opinião humana.

Estes dados complementam a base de dados SQL (preços e métricas), permitindo enriquecer o sistema com contexto qualitativo.

É necessário garantir:
- Volume suficiente (>100k registos);
- Relevância para o mercado de skins;
- Acesso viável aos dados.

---

## 2. Opções Consideradas

* Opção 1 - Reddit (API / Web Scraping)
* Opção 2 - Twitter/X API
* Opção 3 - Steam Reviews API
* Opção 4 - Steam Market (Web Scraping)

---

## 3. Decisão

**Utilizar múltiplas fontes: Reddit + Steam Market (via Web Scraping)**

---

## 4. Justificação

A decisão privilegia fontes com maior relevância direta para o mercado de skins.

### Reddit:
- Comunidades ativas (ex: trading, investimento, skins);
- Alto valor semântico (discussões, opiniões, previsões);
- Dados ideais para análise de sentimento e contexto.

### Steam Market (Scraping):
- Dados diretamente relacionados com listings e atividade de mercado;
- Informação complementar ao SQL (preço + contexto);
- Permite captar comportamento real dos utilizadores.

### Alternativas rejeitadas:
- **Twitter/X**: Acesso restrito e elevado custo;
- **Steam Reviews**: Pouco relevante para análise de mercado de skins (focado em jogos, não trading).

A utilização combinada de múltiplas fontes melhora a qualidade do RAG e reduz viés nos dados.

---

## 5. Consequências

### Positivas
- Maior relevância dos dados para o problema;
- Melhor qualidade semântica para RAG;
- Capacidade de análise de sentimento mais rica;
- Diversificação de fontes (reduz dependência);
- Melhor suporte à decisão.

### Negativas
- Complexidade adicional (web scraping);
- Possíveis bloqueios ou alterações nas fontes;
- Necessidade de limpeza e filtragem de dados;
- Gestão de múltiplas pipelines de ingestão.

### Mitigações
- Implementar scraping com controlo de frequência;
- Criar filtros para remover dados irrelevantes;
- Monitorizar falhas nas fontes;
- Manter arquitetura modular para substituir fontes facilmente.