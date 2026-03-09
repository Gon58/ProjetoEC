import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


from src.services.tools import (  # noqa: E402
    consultar_estatisticas_skin,
    pesquisar_opiniao_comunidade,
)


def main():
    print("\n" + "=" * 50)
    print("🧪 TESTE ÀS TOOLS DO AGENTE (SEMANA 6)")
    print("=" * 50)

    # Teste 1: A Tool do PostgreSQL
    print("\n[1] A testar Tool do SQL (Determinístico)...")
    resultado_sql = consultar_estatisticas_skin("AK-47 | Baroque Purple (Minimal Wear)")
    print(f"Resposta da Tool SQL:\n{resultado_sql}")

    # Teste 2: A Tool do ChromaDB (Semântico)
    print("\n[2] A testar Tool do RAG (Aproximado)...")
    resultado_rag = pesquisar_opiniao_comunidade("O que o pessoal acha da AK-47 Vulcan?")
    print(f"Resposta da Tool RAG:\n{resultado_rag}")

    print("\n" + "=" * 50)
    print("TESTES CONCLUÍDOS")
    print("=" * 50)


if __name__ == "__main__":
    main()

# docker exec -w /app ec-project-app python -m tests.scripts.test_tools