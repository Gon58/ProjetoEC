# Projeto EC

## Descrição

Projeto em desenvolvimento.

## Autores

André Dias

Fernando Pires

Gonçalo Silva

João Costa

Luís Figueiredo

Pedro Teixeira

## Instruções de Uso

1. Duplicar o ficheiro .env.example e renomear a cópia para .env.
2. Substituir os valores falsos pelas credenciais reais no ficheiro .env.
3. Correr docker-compose up.

## Carga Completa de Dados no Docker

Para arrancar os serviços e carregar dados para PostgreSQL, MongoDB e ChromaDB:

```bash
python scripts/load_all_data_docker.py
```

Modo por omissão: usa um limite automático para manter a recolha/indexação perto de 30 minutos.

Para tentar a carga total (pode demorar bastante mais):

```bash
python scripts/load_all_data_docker.py --full
```

Exemplo com limite explícito:

```bash
python scripts/load_all_data_docker.py --steam-target-total 5000 --index-limit 1500
```
