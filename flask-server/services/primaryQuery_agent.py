from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from sqlalchemy import text
from models.model import QueryRequest, QueryResponse
from utils.tools import extract_sql_query_from_response, get_relevant_table_info  # Función de extração de SQL
import json
from utils.tools import carregar_exemplos_string

# Configuración del modelo
llm = ChatOllama(model="llama3:8b", temperature=0)

# Cargar ejemplos
exemplos_string = carregar_exemplos_string('utils/exemplos.json')

# Configuración de la base de datos (usando SQLDatabase)
database_uri = "mssql+pyodbc://@RAPHAEL_PC/Teste_RAG?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
db = SQLDatabase.from_uri(database_uri)

# Plantilla del prompt
template = """template = 
    ### TASK
    Given an input question, generate a syntactically correct SQL query for SQL Server.

    ### DATABASE SCHEMA
    {table_info}

    ### PARAMETERS
    Consider at most {top_k} relevant tables.

    ### USER QUESTION
    {input}

    ### EXAMPLES
    {exemplos_string}

    ### INSTRUCTIONS
    Before generating the query, carefully review the provided EXAMPLES to ensure the query matches the patterns in these examples.
    
    - The name of the employee or the entity in the question might vary, and the question can be phrased in different ways or in different languages (e.g., Portuguese, Spanish, English).
    - **Extract the relevant name or entity** from the question. This could be an employee's name like João, or other relevant entities like "salary", "product", etc.
    - The same query should be generated regardless of the phrasing. For example:
      - "Qual o salário de João?"
      - "¿Cuál es el salario de João?"
      - "What is João's salary?"
      Should all generate the same SQL query to retrieve João's salary from the database.
    - **Interpret** the question semantically: Identify what is being asked (e.g., salary of an employee, total sales of a product) and generate the SQL query based on the extracted entity from the question.
    - If the user is asking about a specific person (e.g., "João"), **generate a query using that name** extracted from the question. For example, if the question is "What is João's salary?", the query should return João's salary from the database.

    Make sure to match the syntax and operations commonly used in SQL Server, such as **DATEDIFF**, **CAST**, **SUM**, etc., for handling dates, numbers, or specific calculations like salary or FGTS.

    ### IMPORTANT
    - Return ONLY the SQL query. Do NOT provide any additional explanation or comments.
    - Do NOT use columns or tables that are not present in the DATABASE SCHEMA section.
    - The output must be ONLY the SQL query, with no leading or trailing text.
"""

# Crear el prompt
prompt = PromptTemplate(
    input_variables=["input", "top_k", "table_info", "exemplos_string"],
    template=template
)

# Crear la cadena (chain)
chain = LLMChain(llm=llm, prompt=prompt)

# Función para generar la consulta SQL
def generate_sql_query(query_request: QueryRequest) -> QueryResponse:
    print("Entramos na IA1")
    raw_query = None
    table_info = get_relevant_table_info(db)
    try:
        # Ejecutar el modelo
        result = chain.invoke({
            "input": query_request.question,
            "table_info": table_info,
            "top_k": 20,
            "exemplos_string": exemplos_string  # Pasa los ejemplos al modelo
        })

        text_response = result["text"]

        # Extraer la query generada
        raw_query = extract_sql_query_from_response(text_response)
        print("Query extraida IA1: ",raw_query)
 

        print("Executando a consulta no banco de dados...")
        with db._engine.connect() as conn:
            result = conn.execute(text(raw_query)).fetchall()
            if isinstance(result, list) and all(hasattr(row, "_mapping") for row in result):
                result_data = [
                    {k: str(v) for k, v in row._mapping.items()}
                    for row in result
                ]
                if not result_data:
                    print("⚠️ A IA1 executou a query corretamente, mas não retornou resultados.")
                    return raw_query, "NO_RESULTS_FOUND"
            else:
                print("⚠️ Resultado inválido. A IA1 retornou algo inesperado.")
                return raw_query, "INVALID_RESULT_FORMAT"

        print(f"Consulta executada com sucesso no banco de dados. Result: {result_data}")

        # Retorna tanto la consulta generada como los datos de la ejecución
        return {"query": raw_query, "result_data": result_data}

    except Exception as e:
        print(f"❌ Erro ao executar o processo: {e}")
        # Devuelve tag estandarizado para que la IA2 lo entienda
        return raw_query, "SQL_ERROR_OCCURRED"

