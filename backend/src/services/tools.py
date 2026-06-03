import logging
import re

import psycopg
from dotenv import load_dotenv

from ..core.config import POSTGRES_URL, RAG_COLLECTION_NAME
from ..core.prompts import get_prompt

load_dotenv()

logger = logging.getLogger(__name__)

_WEAR_ALIASES = {
    "fn": "Factory New",
    "mw": "Minimal Wear",
    "ft": "Field-Tested",
    "ww": "Well-Worn",
    "bs": "Battle-Scarred",
}

_WEAR_ALIAS_RE = re.compile(
    r"\(\s*(" + "|".join(_WEAR_ALIASES) + r")\s*\)",
    flags=re.IGNORECASE,
)


def _normalize_skin_name(nome_skin: str) -> str:
    """Expands wear-state abbreviations so the SQL query finds the skin."""
    return _WEAR_ALIAS_RE.sub(
        lambda m: f"({_WEAR_ALIASES[m.group(1).lower()]})",
        nome_skin,
    )


def consultar_estatisticas_skin(nome_skin: str) -> str:
    """Consulta estatisticas exatas de mercado de uma skin no PostgreSQL."""

    if not POSTGRES_URL:
        return get_prompt(
            "tools.consultar_estatisticas_skin.errors.missing_postgres_url",
            "Erro tecnico: Variavel POSTGRES_URL nao esta configurada no .env",
        )

    nome_skin = _normalize_skin_name(nome_skin)
    postgres_url_limpo = POSTGRES_URL.replace("postgresql+psycopg://", "postgresql://")

    try:
        with psycopg.connect(postgres_url_limpo) as conn:
            with conn.cursor() as cur:
                base_select = """
                    SELECT s.min_price, s.max_price, s.mean_price, s.quantity_sold,
                           s.currency, s.last_updated,
                           (SELECT MAX(recorded_at) FROM skin_price_history
                            WHERE skin_id = s.id) AS latest_record
                    FROM skin s
                """
                # Try exact match first, then case-insensitive fallback.
                cur.execute(base_select + "WHERE s.name = %s LIMIT 1", (nome_skin,))
                resultado = cur.fetchone()
                if not resultado:
                    fallback = "WHERE LOWER(s.name) = LOWER(%s) LIMIT 1"
                    cur.execute(base_select + fallback, (nome_skin,))
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
                        mean_p=f"{mean_p:.2f}",
                        min_p=f"{min_p:.2f}",
                        max_p=f"{max_p:.2f}",
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


def pesquisar_opiniao_comunidade(topico: str) -> str:
    """Searches community sentiment from Reddit posts, comments, and Steam reviews.

    Queries three ChromaDB collections in order (reddit_posts, reddit_comments,
    steam_reviews), deduplicates the retrieved snippets, and returns the top 5
    as a pipe-separated string for the LLM to synthesise.

    Args:
        topico: A descriptive search phrase, e.g. "Vale a pena investir em Dragon Lore".

    Returns:
        A prefixed string of community opinion snippets, or a not-found message
        if no relevant results were retrieved.
    """
    from ..db.vectorial import search_documents

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
            logger.warning("RAG search failed for collection %s: %s", collection_name, e)
            continue
    
    if textos:
        seen: set[str] = set()
        unique: list[str] = []
        for t in textos:
            if t not in seen:
                seen.add(t)
                unique.append(t)

        prefix = get_prompt(
            "tools.pesquisar_opiniao_comunidade.responses.success_prefix",
            "Opinioes da comunidade: ",
        )
        return prefix + " | ".join(unique[:5])
    
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