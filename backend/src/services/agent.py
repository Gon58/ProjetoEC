import ollama

from .embeddings import ensure_model, get_ollama_client 
from .tools import consultar_estatisticas_skin, pesquisar_opiniao_comunidade
from ..core.config import LLM_MODEL
from ..core.prompts import get_prompt

def load_system_prompt() -> str:
    return get_prompt("llm.system_prompt", "")

def chat_nesy_agent(mensagem_utilizador: str) -> str:
    """
    O Router Neuro-Simbólico principal.
    """

    print(f"A verificar/instalar o modelo {LLM_MODEL} no Docker...")
    ensure_model(LLM_MODEL)
    
    client = get_ollama_client()
    system_prompt = load_system_prompt()
    
    mensagens = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": mensagem_utilizador}
    ]
    
    ferramentas_disponiveis = {
        "consultar_estatisticas_skin": consultar_estatisticas_skin,
        "pesquisar_opiniao_comunidade": pesquisar_opiniao_comunidade
    }
    
    print(f"\n[Agente] A analisar a pergunta: '{mensagem_utilizador}'")
    
    # router
    resposta_llm = client.chat(
        model=LLM_MODEL,
        messages=mensagens,
        tools=[consultar_estatisticas_skin, pesquisar_opiniao_comunidade]
    )
    
    mensagens.append(resposta_llm["message"])
    
    # verificar se o LLM decidiu chamar alguma ferramenta
    if resposta_llm.get("message", {}).get("tool_calls"):
        for tool_call in resposta_llm["message"]["tool_calls"]:
            nome_da_tool = tool_call["function"]["name"]
            argumentos = tool_call["function"]["arguments"]
            
            print(f"[Router] O LLM escolheu a rota: {nome_da_tool}")
            
            funcao_python = ferramentas_disponiveis.get(nome_da_tool)
            if funcao_python:
                resultado_bruto = funcao_python(**argumentos)
                
                mensagens.append({
                    "role": "tool",
                    "content": str(resultado_bruto),
                    "name": nome_da_tool
                })
                
        # resposta final
        resposta_final = client.chat(
            model=LLM_MODEL,
            messages=mensagens
        )
        return resposta_final["message"]["content"]
        
    return resposta_llm["message"]["content"]
