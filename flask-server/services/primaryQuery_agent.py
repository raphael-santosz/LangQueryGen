from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from sqlalchemy import text
from models.model import QueryRequest
from utils.tools import carregar_prompt, extract_sql_query_from_response, get_relevant_table_info, carregar_exemplos_string
import json

# Configuración del modelo
llm = ChatOllama(model="llama3:8b", temperature=0)

# Cargar ejemplos
exemplos_string = carregar_exemplos_string('utils/exemplos.json')

# Configuración de la base de datos (usando SQLDatabase)
database_uri = "mssql+pyodbc://@RAPHAEL_PC/Teste_RAG?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
db = SQLDatabase.from_uri(database_uri)

# Función para generar la consulta SQL
def generate_sql_query(query_request: QueryRequest):
    print("Entramos na IA1")
    raw_query = None
    table_info = get_relevant_table_info(db)

    try:
        # Escoge el prompt basado en el nivel de acceso
        if query_request.access_level == "Funcionário":
            template_str = carregar_prompt("prompts/lowAccess_primary.txt")
        else:
            template_str = carregar_prompt("prompts/highAccess_primary.txt")

        prompt = PromptTemplate(
            input_variables=["input", "top_k", "table_info", "exemplos_string"],
            template=template_str
        )
        chain = LLMChain(llm=llm, prompt=prompt)

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

