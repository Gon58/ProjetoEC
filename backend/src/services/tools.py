import psycopg
from dotenv import load_dotenv

from ..core.config import POSTGRES_URL, RAG_COLLECTION_NAME
from ..core.prompts import get_prompt

load_dotenv()


def consultar_estatisticas_skin(nome_skin: str) -> str:
    """Consulta estatisticas exatas de mercado de uma skin no PostgreSQL."""

    if not POSTGRES_URL:
        return get_prompt(
            "tools.consultar_estatisticas_skin.errors.missing_postgres_url",
            "Erro tecnico: Variavel POSTGRES_URL nao esta configurada no .env",
        )

    postgres_url_limpo = POSTGRES_URL.replace("postgresql+psycopg://", "postgresql://")

    try:
        with psycopg.connect(postgres_url_limpo) as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT s.min_price, s.max_price, s.mean_price, s.quantity_sold,
                           s.currency, s.last_updated,
                           (SELECT MAX(recorded_at) FROM skin_price_history
                            WHERE skin_id = s.id) AS latest_record
                    FROM skin s
                    WHERE s.name = %s
                    LIMIT 1
                """
                cur.execute(query, (nome_skin,))
                resultado = cur.fetchone()

                if resultado:
                    min_p, max_p, mean_p, qtd, moeda, last_upd, latest_rec = resultado
                    ts = latest_rec or last_upd
                    
                    months = [
                        "janeiro", "fevereiro", "março", "abril", "maio", "junho",
                        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
                    ]
                    ts_str = (
                        f"{ts.day} de {months[ts.month - 1]} de {ts.year},"
                        f" às {ts.strftime('%H:%M')}"
                        if ts else "data desconhecida"
                    )
                    
                    template = get_prompt(
                        "tools.consultar_estatisticas_skin.responses.success",
                        (
                            "Dados exatos de mercado para a skin '{nome_skin}':\n"
                            "- Preco Medio: {mean_p} {moeda}\n"
                            "- Preco Minimo: {min_p} {moeda}\n"
                            "- Preco Maximo: {max_p} {moeda}\n"
                            "- Quantidade Vendida: {qtd} unidades.\n"
                            "- Dados lidos em: {ts_str}"
                        ),
                    )
                    return template.format(
                        nome_skin=nome_skin,
                        mean_p=mean_p,
                        min_p=min_p,
                        max_p=max_p,
                        qtd=qtd,
                        moeda=moeda,
                        ts_str=ts_str,
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
    """Searches community context from Reddit and Steam reviews."""
    from src.db.vectorial import search_documents

    textos = []

    # Busca posts e comentarios do Reddit, depois Steam.
    for collection_name in ["reddit_posts", "reddit_comments", RAG_COLLECTION_NAME]:
        try:
            resultado = search_documents(
                query=topico, 
                collection_name=collection_name, 
                n_results=3
            )
            if resultado.get("status") == "success" and resultado.get("results"):
                textos.extend([res["text"] for res in resultado["results"]])
        except Exception as e:
            print(f"Erro ao buscar em {collection_name}: {e}")
            continue
    
    if textos:
        prefix = get_prompt(
            "tools.pesquisar_opiniao_comunidade.responses.success_prefix",
            "Opinioes da comunidade: ",
        )
        return prefix + " | ".join(textos[:5])
    
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