import psycopg
import os

from dotenv import load_dotenv

load_dotenv()


def consultar_estatisticas_skin(nome_skin: str) -> str:
    """
    ÚTIL APENAS PARA DADOS DETERMINÍSTICOS E MATEMÁTICOS DE MERCADO.
    Usa esta ferramenta SEMPRE que o utilizador perguntar por:
    - Preços exatos (mínimo, máximo, média).
    - Quantidade de vendas / volume de mercado de uma skin.
    NÃO USES esta ferramenta para procurar opiniões ou sentimentos do Reddit.
    
    Args:
        nome_skin (str): O nome exato da skin de CS:GO (ex: 'AK-47 | Baroque Purple (Minimal Wear)').
    """

    postgres_url = os.getenv("POSTGRES_URL")
    
    if not postgres_url:
        return "Erro técnico: Variável POSTGRES_URL não está configurada no .env"
    
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
                    return (
                        f"Dados exatos de mercado para a skin '{nome_skin}':\n"
                        f"- Preço Médio: {mean_p} {moeda}\n"
                        f"- Preço Mínimo: {min_p} {moeda}\n"
                        f"- Preço Máximo: {max_p} {moeda}\n"
                        f"- Quantidade Vendida: {qtd} unidades."
                    )
                return f"Não encontrei dados de mercado exatos para a skin '{nome_skin}' na base de dados SQL."
    except Exception as e:
        return f"Erro técnico ao consultar a base de dados SQL: {e}"


# FERRAMENTA 2: A ponte para o RAG (Textos e Opiniões)
def pesquisar_opiniao_comunidade(topico: str) -> str:
    """
    ÚTIL APENAS PARA CONTEXTO SEMÂNTICO E OPINIÕES.
    Usa esta ferramenta SEMPRE que o utilizador perguntar por:
    - O que a comunidade acha de uma skin.
    - Se vale a pena investir (baseado em sentimento).
    - Opiniões do Reddit ou fóruns.
    NÃO USES esta ferramenta para procurar preços exatos ou matemática.
    
    Args:
        topico (str): O tema a pesquisar (ex: 'Opiniões sobre a nova caixa').
    """
    # Função que chama a busca vetorial no ChromaDB para obter opiniões relevantes do Reddit ou fóruns.
    from src.db.vectorial import search_documents
    
    resultado = search_documents(query=topico, collection_name="reddit_posts", n_results=3)
    if resultado["status"] == "success":
        # Junta todos os textos encontrados para o LLM ler
        textos = [res["text"] for res in resultado["results"]]
        return "Opiniões da comunidade: " + " | ".join(textos)
    
    return "Não encontrei opiniões relevantes."