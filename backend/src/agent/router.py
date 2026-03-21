from src.services.tools import consultar_estatisticas_skin, pesquisar_opiniao_comunidade
from src.core.prompts import get_prompt

# from src.services.agent import invocar_llm 

class NeSyRouter:
    def __init__(self):
        self.system_prompt = get_prompt("llm.system_prompt", "")

    def processar_pergunta(self, pergunta_utilizador: str) -> str:
        """
        O coração do agente: recebe a pergunta, decide a tool, executa e responde.
        """
        print(f"\n👤 Utilizador: {pergunta_utilizador}")
        
            #! placeholder, assume que a função devolve a tool a usar
        decisao_llm = invocar_llm(
            prompt=pergunta_utilizador,
            system_prompt=self.system_prompt,
            tools_disponiveis=["consultar_estatisticas_skin", "pesquisar_opiniao_comunidade"]
        )

            # router
        nome_tool = decisao_llm.get("tool_escolhida")
        argumentos = decisao_llm.get("argumentos", {})

        if nome_tool == "consultar_estatisticas_skin":
            print("[Router] Caminho Factual detetado -> A consultar SQL")
            dados_brutos = consultar_estatisticas_skin(nome_skin=argumentos.get("nome_skin", ""))
            
        elif nome_tool == "pesquisar_opiniao_comunidade":
            print("[Router] Caminho Opinião/Sentimento detetado -> A consultar Vector Search (RAG)")
            dados_brutos = pesquisar_opiniao_comunidade(topico=argumentos.get("topico", ""))
            
        else:
            print("[Router] Nenhuma tool necessária. A responder diretamente")
            return decisao_llm.get("resposta_texto")

        # NeSy: Fusão dos dados obtidos para resposta final
        prompt_final = (
            f"Pergunta original do utilizador: {pergunta_utilizador}\n"
            f"Dados obtidos pela ferramenta: {dados_brutos}\n"
            f"Por favor, formula a resposta final baseada APENAS nestes dados."
        )
        
        resposta_final = invocar_llm(
            prompt=prompt_final,
            system_prompt=self.system_prompt
        )
        
        return resposta_final.get("resposta_texto")