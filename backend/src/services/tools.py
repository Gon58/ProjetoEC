import os

import psycopg
from dotenv import load_dotenv

from src.services.prompts import get_prompt

load_dotenv()


def consultar_estatisticas_skin(nome_skin: str) -> str:
    """Consulta estatisticas exatas de mercado de uma skin no PostgreSQL."""

    postgres_url = os.getenv("POSTGRES_URL")

    if not postgres_url:
        return get_prompt(
            "tools.consultar_estatisticas_skin.errors.missing_postgres_url",
            "Erro tecnico: Variavel POSTGRES_URL nao esta configurada no .env",
        )

    postgres_url_limpo = postgres_url.replace("postgresql+psycopg://", "postgresql://")

    try:
        with psycopg.connect(postgres_url_limpo) as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT min_price, max_price, mean_price, quantity_sold, currency 
                    FROM skin 
                    WHERE name = %s 
                    LIMIT 1
                """
                cur.execute(query, (nome_skin,))
                resultado = cur.fetchone()

                if resultado:
                    min_p, max_p, mean_p, qtd, moeda = resultado
                    template = get_prompt(
                        "tools.consultar_estatisticas_skin.responses.success",
                        (
                            "Dados exatos de mercado para a skin '{nome_skin}':\n"
                            "- Preco Medio: {mean_p} {moeda}\n"
                            "- Preco Minimo: {min_p} {moeda}\n"
                            "- Preco Maximo: {max_p} {moeda}\n"
                            "- Quantidade Vendida: {qtd} unidades."
                        ),
                    )
                    return template.format(
                        nome_skin=nome_skin,
                        mean_p=mean_p,
                        min_p=min_p,
                        max_p=max_p,
                        qtd=qtd,
                        moeda=moeda,
                    )

                template = get_prompt(
                    "tools.consultar_estatisticas_skin.responses.not_found",
                    (
                        "Nao encontrei dados de mercado exatos para a skin "
                        "'{nome_skin}' na base de dados SQL."
                    ),
                )
                return template.format(nome_skin=nome_skin)
    except Exception as e:
        template = get_prompt(
            "tools.consultar_estatisticas_skin.errors.technical_error",
            "Erro tecnico ao consultar a base de dados SQL: {error}",
        )
        return template.format(error=e)


# FERRAMENTA 2: A ponte para o RAG (Textos e Opiniões)
def pesquisar_opiniao_comunidade(topico: str) -> str:
    """Pesquisa opiniao e contexto semantico da comunidade via busca vetorial."""
    # Função que chama a busca vetorial no ChromaDB para obter
    # opiniões relevantes do Reddit ou fóruns.
    from src.db.vectorial import search_documents

    resultado = search_documents(query=topico, collection_name="reddit_posts", n_results=3)
    if resultado["status"] == "success":
        # Junta todos os textos encontrados para o LLM ler
        textos = [res["text"] for res in resultado["results"]]
        prefix = get_prompt(
            "tools.pesquisar_opiniao_comunidade.responses.success_prefix",
            "Opinioes da comunidade: ",
        )
        return prefix + " | ".join(textos)

    return get_prompt(
        "tools.pesquisar_opiniao_comunidade.responses.not_found",
        "Nao encontrei opinioes relevantes.",
    )


consultar_estatisticas_skin.__doc__ = get_prompt(
    "tools.consultar_estatisticas_skin.docstring",
    consultar_estatisticas_skin.__doc__ or "",
)

pesquisar_opiniao_comunidade.__doc__ = get_prompt(
    "tools.pesquisar_opiniao_comunidade.docstring",
    pesquisar_opiniao_comunidade.__doc__ or "",
)