import json
import logging
from typing import Any

from .embeddings import ensure_model, get_ollama_client 
from .tools import consultar_estatisticas_skin, pesquisar_opiniao_comunidade
from ..core.config import LLM_MODEL
from ..core.prompts import get_prompt


logger = logging.getLogger(__name__)


def _log_event(event: str, payload: dict[str, Any]) -> None:
    logger.info(json.dumps({"event": event, **payload}, ensure_ascii=False, default=str))

def load_system_prompt() -> str:
    return get_prompt("llm.system_prompt", "")

def chat_nesy_agent(mensagem_utilizador: str) -> str:
    """
    O Router Neuro-Simbólico principal.
    """

    print(f"A verificar/instalar o modelo {LLM_MODEL} no Docker...")
    _log_event("agent_input", {"message": mensagem_utilizador, "model": LLM_MODEL})
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
            _log_event(
                "agent_tool_selected",
                {"tool": nome_da_tool, "arguments": argumentos, "message": mensagem_utilizador},
            )
            
            funcao_python = ferramentas_disponiveis.get(nome_da_tool)
            if funcao_python:
                resultado_bruto = funcao_python(**argumentos)
                _log_event(
                    "agent_tool_result",
                    {
                        "tool": nome_da_tool,
                        "result": str(resultado_bruto),
                        "message": mensagem_utilizador,
                    },
                )
                
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
        resposta_texto = resposta_final["message"]["content"]
        _log_event("agent_output", {"message": mensagem_utilizador, "output": resposta_texto})
        return resposta_texto
        
    resposta_texto = resposta_llm["message"]["content"]
    _log_event("agent_output", {"message": mensagem_utilizador, "output": resposta_texto})
    return resposta_texto
