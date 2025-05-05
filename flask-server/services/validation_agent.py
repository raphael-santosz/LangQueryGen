from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import PromptTemplate
from sqlalchemy.sql import text
from utils.tools import extract_sql_query_from_response  # Importando a função de extração

# Configurações do modelo e banco
llm = ChatOllama(model="mistral", temperature=0)
db = SQLDatabase.from_uri("mssql+pyodbc://@RAPHAEL_PC/Teste_RAG?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server")

def validate_and_refine_query(user_question: str, generated_query: str, query_results: list) -> str:
    """
    Recebe a pergunta do usuário, a query gerada pela IA1 e os resultados da consulta ao banco.
    Verifica se a query é adequada e a refina se necessário, retornando uma nova query refinada.
    """
    # Prompt para validar e ajustar a query
    template = """
    A partir da seguinte pergunta do usuário: {user_question}, temos a seguinte query SQL gerada: {generated_query}. 
    Os resultados da consulta ao banco de dados foram: {query_results}.
    O objetivo é verificar se a query gerada responde de forma correta e precisa à pergunta do usuário, considerando os resultados do banco.      
    Se necessário, faça ajustes e refinações na query para torná-la mais adequada, sem alterar seu sentido original.
    
    Retorne apenas a query SQL gerada ou ajustada, sem a necessidade de explicar sua validade.
    """
    
    prompt = PromptTemplate(input_variables=["user_question", "generated_query", "query_results"], template=template)
    
    # Formatação do prompt
    formatted_prompt = prompt.format(user_question=user_question, generated_query=generated_query, query_results=query_results)
    
    print(f"🔍 Antes de chamar invoke: {formatted_prompt}")  
    
    try:
        # Chama o modelo para executar a query gerada ou ajustada
        result = llm.invoke(formatted_prompt)
        print(f"🔍 Resultado após invoke: {result}")
        
        query = extract_sql_query_from_response(result)
        
        # Executando a consulta no banco de dados
        with db._engine.connect() as conn:
            result = conn.execute(text(query)).fetchall()
            refined_result_data = [
                {k: str(v) for k, v in row._mapping.items()}
                for row in result
            ]
            
            # Se não houver resultados, passamos a mensagem para a IA3
            if not refined_result_data:
                print("⚠️ A IA2 não retornou resultados para a query gerada. Passando para a IA3...")
                return "Não foi possível encontrar dados relacionados à sua pergunta."

            print(f"📊 Resultados da query refinada: {refined_result_data}")
            return query, refined_result_data  # Retorna a query gerada e os dados encontrados no banco
        
    except Exception as e:
        print(f"❌ Erro ao executar o processo: {e}")
        return "Ocorreu um erro ao tentar processar sua solicitação."
