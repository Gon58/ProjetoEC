# ADR 012: Seleção do Modelo LLM (qwen2.5:7b)

**Data:** 2026-04-27 (Revisão)

**Status:** Aceite

**Responsável/Autores:** André Carvalho, João Costa

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

Foi escolhido o modelo `qwen2.5:7b` como modelo LLM principal do backend, baseado em testes comparativos realizados em 2026-04-26.

---

## 4. Justificação

`qwen2.5:7b` demonstrou superioridade em testes práticos comparativos com `llama3.1:8b`, apresentando:

- **Precisão em tool-calling**: 3/3 acertos em todas as rotas (SQL, RAG, Híbrida) e benchmark SQL, vs 2/3 no llama em rotas híbridas;
- **Ausência de alucinações**: Mantém fidelidade aos outputs das tools, sem inventar valores;
- **Consistência em routing**: Cumpre corretamente chamadas múltiplas de tools na mesma turno;
- **Disponibilidade**: Integração simples via Ollama no ambiente Docker;
- **Performance aceitável**: Tempos de resposta comparáveis para a fase MVP (~53-115s dependendo rota).

Trade-offs:

- Pode exigir mais recursos que modelos mais leves;
- Qualidade depende da versão/model card disponível no host Ollama;
- Performance com VRAM reduzida (8GB) pode impactar latência.

---

## 6. Testes Comparativos e Validação

### Modelos Avaliados

Testados via Ollama em 2026-04-26 | Framework: Assistente de mercado CS2 (tools SQL + RAG)

| Modelo | Status | Tool Calling |
|---|---|---|
| `qwen2.5:7b` | Testado | Funcional |
| `llama3.1:8b` | Testado | Funcional |
| `mistral:7b-instruct` | Excluído | Não suportado via Ollama |
| `gemma2:9b` | Excluído | Não suportado via Ollama |
| `phi3:medium` | Excluído | Não suportado via Ollama |

`mistral:7b-instruct`, `gemma2:9b` e `phi3:medium` foram descartados antes dos testes uma vez que nenhum consegue invocar tools através da API do Ollama, tornando-os inviáveis para o nosso caso.

### Suite de Testes

Três rotas foram testadas com 3 perguntas cada:

- **SQL** — chamada única de tool para recuperar preço mín/máx/médio e quantidade vendida
- **RAG** — chamada única de tool para buscar sentimento da comunidade
- **Híbrida** — ambas as tools devem ser chamadas na mesma turno

Um **Benchmark SQL** separado (3 perguntas) testou recuperação de dados contra valores esperados conhecidos.

### Precisão em Tool-Calling

| Rota | qwen2.5:7b | llama3.1:8b |
|---|---|---|
| SQL | 3/3 | 3/3 |
| RAG | 3/3 | 3/3 |
| Híbrida | 3/3 | 2/3 |
| Benchmark SQL | 3/3 | 2/3 |

O erro do Llama em rotas híbridas ocorreu em `hybrid_q2` — chamou apenas a tool RAG e pulou SQL completamente. A falha em benchmark SQL resultou de anexar `(Factory New)` a um nome de skin que não o requeria, retornando zero resultados. Um artefato de formatação (linha de caracteres `═` como resposta) foi também observado em benchmark q3.

### Deteção de Alucinações

No teste SQL, qwen conseguiu output dos resultados das tools como eram, sem inventar valores (a mensagem do modelo nunca se afastou muito do output da tool, provavelmente devido a temperatura baixa). Entretanto, Llama, apesar de chamar as tools bem (2/3 vezes), nunca conseguiu pegar nos outputs das tools e transmiti-los ao utilizador final.

### Tempos de Resposta (média em segundos)

| Rota | qwen2.5:7b | llama3.1:8b |
|---|---|---|
| SQL (multi-modelo) | ~74.5s | ~70.2s |
| RAG (multi-modelo) | ~69.9s | ~87.5s |
| Híbrida (multi-modelo) | ~115.3s | ~93.1s |
| Benchmark SQL | ~53.3s | ~89.6s* |

*A média de Llama em benchmark SQL está inflacionada por um erro resultante de uma chamada SQL fraca em q1, causando timeout, aumentando assim a média.

Estes tempos são bastante semelhantes entre modelos, mas deve-se notar que os testes foram realizados em placa com 8GB VRAM, o que certamente não ajudou os tempos a serem mais curtos. Apesar disto, usar modelos mais pequenos (ex: 3B params) provou ser ineficaz — exibem os mesmos problemas que llama3.1:8b.

### Conclusão dos Testes

`qwen2.5:7b` foi o melhor desempenho geral: precisão quase perfeita em tool-calling em todas as rotas, recuperação SQL consistente, e tempos de benchmark mais rápidos. `llama3.1:8b` foi competitivo em chamadas single-tool mas não muito além disso.

Para pipelines agentic que requerem chamadas multi-tool confiáveis, `qwen2.5:7b` é a escolha recomendada entre os modelos testados.

---
