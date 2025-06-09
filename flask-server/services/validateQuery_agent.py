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
llm = ChatOllama(model="llama3:8b", temperature=0)
db = SQLDatabase.from_uri("mssql+pyodbc://@RAPHAEL_PC/Teste_RAG?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server")

def validate_and_refine_query(user_question: str, generated_query: str, query_results: list) -> tuple:
    # Captura a estrutura da base de dados dinamicamente
    table_info = db.get_table_info()
    query = None

    template = """
    ### USER QUESTION
    {user_question}

    ### GENERATED QUERY
    {generated_query}

    ### DATABASE SCHEMA
    {table_info}

    ### EXAMPLES
    {exemplos_string}

    ### QUERY RESULTS
    {query_results}

    ### TASK
    You must verify whether the GENERATED QUERY correctly answers the USER QUESTION, considering the QUERY RESULTS and the DATABASE SCHEMA.
    If necessary, adjust and refine the query to make it more accurate, without changing the original intent of the USER QUESTION.

    ### IMPORTANT
    - Return ONLY the final SQL query. Do NOT provide explanations or comments.
    - Do NOT use columns or tables that are not present in the DATABASE SCHEMA section.
    - The output must be ONLY the SQL query, with no leading or trailing text.
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
        query = None  # ← inicializa aqui
        # Chama o modelo para executar a query gerada ou ajustada
        result = llm.invoke(formatted_prompt)
        print(f"🔍 Resultado após invoke: {result}")
        
        query = extract_sql_query_from_response(result)
        
        # Executando a consulta no banco de dados
        with db._engine.connect() as conn:
            result = conn.execute(text(query)).fetchall()

        # Verificar si el resultado es válido
        if not (isinstance(result, list) and all(hasattr(row, "_mapping") for row in result)):
            print("⚠️ Resultado inválido. A IA retornou algo inesperado.")
            error_message = "Resultado inválido. A IA retornou algo inesperado."
            error_data = [{"error": error_message}]
            return query, error_data

        # Convertir resultados
        refined_result_data = [
            {k: str(v) for k, v in row._mapping.items()}
            for row in result
        ]

        # Verificar si hay datos
        if not refined_result_data:
            print("⚠️ A IA2 não retornou resultados para a query gerada. Passando para a IA3...")
            error_message = "Não foi possível encontrar dados relacionados à sua pergunta."
            error_data = [{"error": error_message}]
            return query, error_data

        # Devolver resultados
        print(f"📊 Resultados da query refinada: {refined_result_data}")
        return query, refined_result_data

        
    except Exception as e:
        print(f"❌ Erro ao executar o processo: {e}")
        # Em vez de retornar uma string no segundo elemento, retorne uma lista com um dicionário de erro
        error_message = "Ocorreu um erro ao tentar processar sua solicitação."
        error_data = [{"error": error_message}]
        return query, error_data
