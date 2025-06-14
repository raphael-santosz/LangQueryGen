from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import PromptTemplate
from sqlalchemy.sql import text
from utils.tools import extract_sql_query_from_response, get_relevant_table_info  # Importando a função de extração
import json
from utils.tools import carregar_exemplos_string

# Exemplos
exemplos_string = carregar_exemplos_string('utils/exemplos.json')

# Configurações do modelo e banco
llm = ChatOllama(model="llama3:8b", temperature=0)
db = SQLDatabase.from_uri("mssql+pyodbc://@RAPHAEL_PC/Teste_RAG?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server")

def validate_and_refine_query(user_question: str, generated_query: str, query_results: list) -> tuple:
    # Captura a estrutura da base de dados dinamicamente
    table_info = get_relevant_table_info(db)
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
    You must act as a validation agent for the GENERATED QUERY, comparing it with the USER QUESTION and the DATABASE SCHEMA.

    Your goal is to verify whether the GENERATED QUERY semantically and completely answers the USER QUESTION.

    ### RULES
    - If the GENERATED QUERY is semantically coherent and fully answers the USER QUESTION, you can return it as is or make minor corrections.
    - If the GENERATED QUERY does not match the intent of the USER QUESTION (for example: asking about hiring date but returning salary or FGTS), you MUST generate a new SQL query that properly answers the USER QUESTION.
    - If it is impossible to generate a valid query based on the USER QUESTION and DATABASE SCHEMA, you MUST return an empty string.

    ### IMPORTANT
    - You are allowed to change or replace the GENERATED QUERY if necessary.
    - You MUST NOT transform a question about one concept (e.g. FGTS) into a query about another concept (e.g. salary), unless the USER QUESTION clearly asks for it.
    - You MUST NOT invent columns or tables not present in the DATABASE SCHEMA.
    - You MUST NOT simplify necessary calculations, but you can correct incorrect ones.
    - You MUST NOT provide explanations or comments — return ONLY the final SQL query (or an empty string if not possible).
    - The output must be ONLY the SQL query, with no leading or trailing text.

    ### FINAL QUERY
    Return ONLY a valid SQL SELECT query, or an empty string if not possible. Do not add any explanation, markdown, or comments.

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
        print(f"🔍 Resultado após invoke: {result.content}")
        query = extract_sql_query_from_response(result)
        print(f"🔍 Query extraida: {query}")
        
        # Executando a consulta no banco de dados
        with db._engine.connect() as conn:
            result = conn.execute(text(query)).fetchall()

        # Verificar si el resultado es válido
        if not (isinstance(result, list) and all(hasattr(row, "_mapping") for row in result)):
            print("⚠️ Resultado inválido. A IA retornou algo inesperado.")
            return query, "SQL_ERROR_OCCURRED" # ← standardized tag for IA3 to detect errors


        # Convertir resultados
        refined_result_data = [
            {k: str(v) for k, v in row._mapping.items()}
            for row in result
        ]

        # Verificar si hay datos
        if not refined_result_data:
            print("⚠️ A IA2 não retornou resultados para a query gerada. Passando para a IA3...")
            return query, "NO_RESULTS_FOUND" # ← standardized tag for IA3 to detect errors


        # Devolver resultados
        print(f"📊 Resultados da query refinada: {refined_result_data}")
        return query, refined_result_data

        
    except Exception as e:
        print(f"❌ Erro ao executar o processo: {e}")
        # En caso de error, devolvemos el tag estandarizado:
        return query, "SQL_ERROR_OCCURRED" # ← standardized tag for IA3 to detect errors

