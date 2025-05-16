from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import PromptTemplate
from sqlalchemy.sql import text
from utils.tools import extract_sql_query_from_response  # Importando a função de extração
import json
from utils.tools import carregar_exemplos_string

# Exemplos
exemplos_string = carregar_exemplos_string('utils/exemplos.json')

# Configurações do modelo e banco
llm = ChatOllama(model="mistral", temperature=0)
db = SQLDatabase.from_uri("mssql+pyodbc://@RAPHAEL_PC/Teste_RAG?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server")

def validate_and_refine_query(user_question: str, generated_query: str, query_results: list) -> tuple:
    # Captura a estrutura da base de dados dinamicamente
    table_info = db.get_table_info()

    template = """
    A partir da seguinte pergunta do usuário: {user_question}, temos a seguinte query SQL gerada: {generated_query}. 

    Informações sobre a estrutura das tabelas: 
    {table_info}

    Exemplos para basear a geração e refino da query: 
    {exemplos_string}

    Os resultados da consulta ao banco de dados foram: {query_results}.

    O objetivo é verificar se a query gerada responde de forma correta e precisa à pergunta do usuário, considerando os resultados do banco e a estrutura dos dados.  
    Se necessário, faça ajustes e refinações na query para torná-la mais adequada, sem alterar seu sentido original.

    Retorne apenas a query SQL gerada ou ajustada, sem a necessidade de explicar sua validade.
    """
    
    prompt = PromptTemplate(
        input_variables=["user_question", "generated_query", "query_results", "table_info", "exemplos_string"],
        template=template
    )

    formatted_prompt = prompt.format(
        user_question=user_question,
        generated_query=generated_query,
        query_results=query_results,
        table_info=table_info,
        exemplos_string=exemplos_string
    )

    
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
                error_message = "Não foi possível encontrar dados relacionados à sua pergunta."
                error_data = [{"error": error_message}]
                return query, error_data

            print(f"📊 Resultados da query refinada: {refined_result_data}")
            return query, refined_result_data  # Retorna a query gerada e os dados encontrados no banco
        
    except Exception as e:
        print(f"❌ Erro ao executar o processo: {e}")
        # Em vez de retornar uma string no segundo elemento, retorne uma lista com um dicionário de erro
        error_message = "Ocorreu um erro ao tentar processar sua solicitação."
        error_data = [{"error": error_message}]
        return query, error_data
