# CS2 Skin Market Intelligence Platform

Uma plataforma de análise de mercado de skins CS2 com inteligência artificial, dados históricos de preços e um chatbot neuro-simbólico.

## Visão Geral

O projeto agrega dados de mercado de skins CS2 (Counter-Strike 2) de múltiplas fontes (Skinport API, Kaggle, Steam Market), armazena histórico de preços, e oferece:

- **Dashboard interativo** com estatísticas de mercado e gráficos de evolução de preços
- **Chatbot NeSy** ("Teacher Bot Connor") que combina pesquisa SQL precisa com RAG semântico sobre reviews Steam e Reddit
- **Pipeline ETL automatizado** via Prefect 3 para ingestão diária de dados
- **Perfil Steam** com inventário CS2 integrado

## Arquitetura

```
┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐
│   Frontend   │    │   Backend    │    │    Data Pipeline     │
│  React+Vite  │◄──►│   FastAPI    │◄──►│  ETL (Skinport,      │
│  Recharts    │    │   port 8080  │    │  Kaggle, Steam)      │
└──────────────┘    └──────┬───────┘    └──────────────────────┘
     port 5173             │
                    ┌──────┼──────────────────────────┐
                    │      │                          │
              ┌─────▼────┐ ┌────────┐ ┌──────────┐ ┌──────────┐
              │PostgreSQL│ │MongoDB │ │ChromaDB  │ │ Ollama   │
              │(skins,   │ │(reviews│ │(vetores  │ │qwen2.5:7b│
              │ histórico│ │ logs)  │ │ RAG)     │ │ nomic-   │
              │ logs)    │ │        │ │          │ │ embed)   │
              └──────────┘ └────────┘ └──────────┘ └──────────┘
```

## Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Frontend | React 19, Vite, Tailwind CSS, Recharts |
| Backend | FastAPI, Python 3.12 |
| Base de dados relacional | PostgreSQL 16 |
| Base de dados documental | MongoDB 7 |
| Base de dados vetorial | ChromaDB |
| LLM local | Ollama — `qwen2.5:7b` |
| Embeddings | `nomic-embed-text` via Ollama |
| Orquestração ETL | Prefect 3 (self-hosted) |
| Containerização | Docker Compose |

## Funcionalidades

### Dashboard
- Cards de estatísticas: total de skins, preço médio, preço mais alto, skin mais popular
- Gráfico de evolução de preços (30/14/7 dias) para as top 5 skins mais caras
- Tabela paginada de todas as skins com preços e volume de vendas

### Chatbot NeSy — Teacher Bot Connor
- Agente neuro-simbólico com dois modos de raciocínio:
  - **SQL (preciso):** consulta estatísticas exactas de preço diretamente do PostgreSQL
  - **RAG (semântico):** pesquisa opiniões da comunidade no ChromaDB (Steam reviews + Reddit)
- Cada resposta inclui o timestamp de quando os dados foram lidos

### Histórico de Preços
- Tabela `skin_price_history` guarda snapshots diários por skin
- Script de mock data gera 30 dias de histórico simulado para demo
- Pipeline real (Prefect) corre diariamente às 03:00 e adiciona novos snapshots

### Pipeline ETL
- Kaggle dataset → CSV
- Skinport API → preços em tempo real
- Steam Market → scraping
- Merge de todas as fontes → PostgreSQL (UPSERT + inserção no histórico)
- Logs detalhados de cada execução visíveis na página `/logs`

## Autores

- André Dias
- Fernando Pires
- Gonçalo Silva
- João Costa
- Luís Figueiredo
- Pedro Teixeira

## Setup Rápido

Ver [SETUP.md](SETUP.md) para instruções detalhadas passo a passo.

```bash
# 1. Configurar ambiente
cp backend/.env.example .env
# Editar .env com a tua Steam API Key

# 2. Lançar todos os serviços
docker compose up -d

# 3. Correr o pipeline de dados (primeira vez)
docker compose run --rm ec-project-tests python /app/data_pipeline/scripts/run_full_pipeline.py

# 4. Gerar histórico mock para a demo
docker compose run --rm ec-project-tests python /app/data_pipeline/scripts/generate_mock_history.py
```

## URLs dos Serviços

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8080 |
| API Docs (Swagger) | http://localhost:8080/docs |
| Prefect UI | http://localhost:4200 |
