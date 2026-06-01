# Setup — Guia Passo a Passo

## Pré-requisitos

| Ferramenta | Versão mínima | Download |
|------------|---------------|---------|
| Docker Desktop | 24+ | https://www.docker.com/products/docker-desktop |
| Git | qualquer | https://git-scm.com |

> O Docker Desktop precisa de estar **em execução** antes de qualquer comando.

---

## 1. Clonar o repositório

```bash
git clone <url-do-repositório>
cd ProjetoEC
```

---

## 2. Configurar variáveis de ambiente

```powershell
# Windows (PowerShell)
Copy-Item backend\.env.example .env
```

```bash
# macOS / Linux
cp backend/.env.example .env
```

Abre o ficheiro `.env` (na raiz do projecto) e preenche:

```env
DB_USER=ec_project
DB_PASSWORD=ec_project_pass
SESSION_SECRET=escolhe-uma-string-secreta-aleatoria

# Opcional — para login Steam e inventário
STEAM_API_KEY=a-tua-chave-da-steam-api
```

> Steam API Key: https://steamcommunity.com/dev/apikey

---

## 3. Lançar todos os serviços

```bash
docker compose up -d
```

Inicia: PostgreSQL, MongoDB, ChromaDB, Ollama, Backend FastAPI, Frontend React, Prefect Server + Worker.

Aguarda 30–60 segundos e verifica que o backend responde:

```bash
curl http://localhost:8080/health
# Deve devolver {"status": "healthy", ...}
```

> **Nota:** O container `ec-project-tests` aparece como "parado" no Docker Desktop — é normal.  
> Não é um serviço contínuo, é um executor de tarefas. O `docker compose run --rm` arranca  
> uma instância temporária, corre o script, e remove-a automaticamente.

---

## 4. Carregar skins na base de dados (PostgreSQL)

O repositório já inclui os dados processados em `data_pipeline/data/processed/`.  
Não é necessário fazer scraping novamente.

```bash
docker compose run --rm ec-project-tests python /app/data_pipeline/scripts/run_load_postgres.py
```

Carrega o ficheiro `combined_data.csv` (Kaggle + Skinport + Steam, ~55 000 skins) para o PostgreSQL com UPSERT.

No final deves ver:
```
Loaded 55918 rows into PostgreSQL
```

---

## 5. Carregar histórico de preços (Steam Market)

O histórico é baseado nas **10 980 skins do Steam Market** com 30 dias de evolução simulada (~329 000 registos).

### Opção A — CSV já existe (situação normal após clone)

Se o ficheiro `data_pipeline/data/processed/skin_price_history.csv` já existir no repositório:

```bash
docker compose run --rm ec-project-tests python /app/data_pipeline/scripts/load_history_from_csv.py
```

Carrega o CSV directamente para a tabela `skin_price_history`. Rápido (~1–2 min).

### Opção B — CSV não existe (primeira vez ou regenerar)

Se o CSV não existir (ou quiseres regenerar o histórico):

```bash
docker compose run --rm ec-project-tests python /app/data_pipeline/scripts/generate_steam_history.py
```

Gera 30 dias de histórico para todas as skins Steam, guarda o CSV **e** insere no PostgreSQL.  
Demora alguns minutos (~329 000 linhas).

Para forçar a regeneração quando já existe histórico na BD:

```bash
docker compose run --rm ec-project-tests python /app/data_pipeline/scripts/generate_steam_history.py --force
```

No final deves ver:
```
Done.
  329,400 history rows inserted into PostgreSQL.
  CSV saved to: /app/data_pipeline/data/processed/skin_price_history.csv
```

---

## 6. Verificar que tudo está carregado

```bash
# Skins carregadas (~55 000)
docker exec ec-project-postgres psql -U ec_project -d ec_project -c "SELECT source, COUNT(*) FROM skin GROUP BY source ORDER BY COUNT(*) DESC;"

# Histórico de preços (~329 000)
docker exec ec-project-postgres psql -U ec_project -d ec_project -c "SELECT COUNT(*) FROM skin_price_history;"
```

Ou abre o dashboard em http://localhost:5173 — as cards de estatísticas devem ter valores e o gráfico "Price History" deve mostrar linhas com evolução de preços.

---

## 7. (Opcional) Ingestão de dados Reddit para o chatbot

O chatbot NeSy usa RAG sobre reviews Steam e posts Reddit. Para indexar posts Reddit:

### 7.1 Obter credenciais Reddit

1. Vai a https://www.reddit.com/prefs/apps
2. Clica **"create another app"** → tipo **script**
3. Guarda o **client_id** e o **client_secret**

### 7.2 Adicionar ao `.env`

```env
REDDIT_CLIENT_ID=o-teu-client-id
REDDIT_CLIENT_SECRET=o-teu-client-secret
```

### 7.3 Correr a ingestão

```bash
# Passo 1: Descarregar posts do Reddit para MongoDB
docker compose run --rm -e RUN_REDDIT_INGESTION=true ec-project-tests python /app/data_pipeline/scripts/run_full_pipeline.py

# Passo 2: Indexar no ChromaDB (para o RAG do chatbot)
docker compose run --rm -e RUN_REDDIT_VECTOR_INDEXING=true ec-project-tests python /app/data_pipeline/scripts/run_full_pipeline.py
```

---

## 8. Aceder à plataforma

| Serviço | URL | Descrição |
|---------|-----|-----------|
| **Frontend** | http://localhost:5173 | Dashboard, chatbot, perfil |
| **Backend API** | http://localhost:8080 | API REST |
| **Swagger UI** | http://localhost:8080/docs | Documentação interactiva da API |
| **Prefect UI** | http://localhost:4200 | Orquestração e histórico de runs |

---

## 9. Ingestão diária automática (Prefect)

O Prefect Worker corre o pipeline todos os dias às **03:00** (cron `0 3 * * *`).  
Para disparar manualmente:

1. Abre http://localhost:4200
2. Vai a **Deployments** → `ingestion`
3. Clica **Quick run**

> O computador precisa de estar ligado para o Prefect executar as runs agendadas.

---

## Resumo — sequência completa de comandos

```bash
# 1. Lançar serviços
docker compose up -d

# 2. Aguardar o backend (30–60 segundos)
curl http://localhost:8080/health

# 3. Carregar skins (~55 000) no PostgreSQL
docker compose run --rm ec-project-tests python /app/data_pipeline/scripts/run_load_postgres.py

# 4a. Carregar histórico de preços a partir do CSV (se existir)
docker compose run --rm ec-project-tests python /app/data_pipeline/scripts/load_history_from_csv.py

# 4b. OU gerar histórico de raiz (se o CSV não existir)
docker compose run --rm ec-project-tests python /app/data_pipeline/scripts/generate_steam_history.py

# 5. Abrir a plataforma
# http://localhost:5173
```

---

## Cenários de Reset

### Apagar apenas o histórico de preços e recarregar

```bash
docker exec ec-project-postgres psql -U ec_project -d ec_project -c "DELETE FROM skin_price_history;"
docker compose run --rm ec-project-tests python /app/data_pipeline/scripts/load_history_from_csv.py
```

### Apagar skins e histórico e recarregar tudo

```bash
docker exec ec-project-postgres psql -U ec_project -d ec_project -c "TRUNCATE skin_price_history, skin CASCADE;"
docker compose run --rm ec-project-tests python /app/data_pipeline/scripts/run_load_postgres.py
docker compose run --rm ec-project-tests python /app/data_pipeline/scripts/load_history_from_csv.py
```

### Reiniciar tudo do zero (APAGA TODOS OS DADOS DOS VOLUMES)

```bash
docker compose down -v
docker compose up -d
# Depois seguir passos 3 e 4 do resumo acima
```

---

## Resolução de Problemas

### "service is not running" ao usar `docker compose exec ec-project-tests`
Usa sempre `docker compose run --rm`. O `exec` só funciona em containers contínuos.

### Gráfico de histórico vazio
Verifica que o histórico foi carregado:
```bash
docker exec ec-project-postgres psql -U ec_project -d ec_project -c "SELECT COUNT(*) FROM skin_price_history;"
```
Se devolver 0, corre o passo 4.

### Ollama demora muito a responder no chat
O modelo `qwen2.5:7b` (~4 GB) é descarregado na primeira chamada:
```bash
docker compose logs -f ec-project-ollama
```

### Frontend não carrega (módulo não encontrado)
Apaga o volume anónimo do node_modules e reconstrói:
```bash
docker compose rm -fsv ec-project-frontend
docker compose build ec-project-frontend
docker compose up -d ec-project-frontend
```

### Alterações ao backend não têm efeito
O backend tem hot-reload activo (uvicorn --reload). Se persistir, reconstrói:
```bash
docker compose build ec-project-backend
docker compose up -d ec-project-backend
```

### Skinport/Steam Market falham com erro 403 no pipeline completo
Normal — a Cloudflare bloqueia containers Docker. O pipeline continua com dados Kaggle.  
Os dados Steam já estão nos CSVs processados, por isso não é necessário fazer scraping de novo.

---

## Estrutura do Projecto

```
ProjetoEC/
├── backend/              # FastAPI + agente NeSy
│   └── src/
│       ├── api/          # Endpoints REST
│       ├── db/           # Queries PostgreSQL, ChromaDB
│       ├── services/     # Agente NeSy, ferramentas, embeddings
│       └── schemas/      # Modelos Pydantic
├── frontend/             # React + Vite
│   └── src/
│       ├── components/   # StatCard, SkinTable, PriceHistoryChart, …
│       ├── pages/        # Dashboard, Chat, Profile, Logs, Investments
│       └── services/     # api.js — cliente HTTP
├── data_pipeline/        # Pipeline ETL
│   ├── data/
│   │   └── processed/    # CSVs prontos a usar:
│   │       ├── combined_data.csv          # ~55 000 skins (todas as fontes)
│   │       ├── skin_price_history.csv     # ~329 000 linhas histórico Steam
│   │       ├── skinport_items.csv         # Skinport (já processado)
│   │       └── steam_market_prices.csv    # Steam Market (já processado)
│   ├── scripts/
│   │   ├── run_load_postgres.py           # Carrega combined_data.csv → PostgreSQL
│   │   ├── load_history_from_csv.py       # Carrega skin_price_history.csv → PostgreSQL
│   │   ├── generate_steam_history.py      # Gera histórico Steam + guarda CSV
│   │   └── run_full_pipeline.py           # Pipeline completo (scraping desde zero)
│   └── src/data_pipeline/
│       ├── ingestion/    # Skinport, Steam Reviews, Reddit
│       ├── processing/   # Kaggle processor
│       └── loaders/      # PostgreSQL loader (UPSERT + histórico)
├── flows/                # Prefect 3 workflows
│   ├── ingestion_flow.py
│   └── deploy.py
├── docker-compose.yml
└── .env                  # Configuração local (não commitado)
```
