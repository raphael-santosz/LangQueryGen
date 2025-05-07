from langchain.schema import AIMessage

def extract_sql_query_from_response(result) -> str:
    """
    Função para extrair a query SQL da resposta da IA.
    Se a resposta for um AIMessage, acessa o campo 'content'. 
    Se for uma string simples, apenas aplica o 'strip' para limpar.
    """
    # Verifica se o resultado é uma instância de AIMessage
    if isinstance(result, AIMessage):
        query = result.content.strip()  # Acessa diretamente o conteúdo da mensagem e aplica strip
    else:
        query = result.strip()  # Caso contrário, trata como string simples
    
    if not query:
        raise ValueError("❌ A resposta da IA não contém uma query SQL válida.")
    
    return query
