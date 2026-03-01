# ADR 006: Padronização de Idioma e Trade-off de Performance da IA

**Data:** 2026-02-25

**Status:** Aceite

**Responsável/Autores:** André Carvalho, João Costa

## 1. Contexto e Problema

Temos de processar texto não estruturado (opiniões no Reddit) e dados de mercado (Steam/Skinport). Todos estes dados de origem estão provenientemente em Inglês. Adicionalmente, ao elaborar a Inteligência NeSy, temos de decidir se priorizamos a precisão absoluta do modelo de linguagem (LLM) ou a latência de resposta, documentando os devidos *trade-offs*.

## 2. Opções Consideradas (Idioma)

* Traduzir todos os dados de ingestão para Português antes de guardar nas bases de dados.
* Manter todos os dados padronizados em Inglês no *Backend*.

## 3. Opções Consideradas (Performance)

* Utilizar modelos pesados para maximizar a precisão da resposta.
* Priorizar modelos mais rápidos para garantir uma boa experiência no *Chat*.

## 4. Decisão e Justificação

**Sobre o Idioma:** Decidimos manter todos os dados na base de dados (SQL, NoSQL e Vetorial) padronizados em **Inglês**. Traduzir ativamente mais de 100k registos consumiria demasiados recursos e tempo. O *Chatbot* fará a ponte, podendo receber perguntas em Português e traduzindo o raciocínio (*prompt*) em *background*.

**Sobre a Performance (Latência vs Precisão):** O foco principal é a Experiência de Decisão na interface. Como o *chat* integrado deve alterar o estado do *dashboard*, uma alta latência destruiria a usabilidade. Portanto, **priorizamos a velocidade (baixa latência)**. Se o sistema estiver lento, ajustaremos a performance optando por modelos mais pequenos ou testando abordagens como PEFT/LORA conforme mencionado anteriormente. A precisão será garantida pelas operações determinísticas no SQL, deixando o LLM focado apenas em resumir rapidamente.
