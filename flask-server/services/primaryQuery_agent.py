from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from sqlalchemy import text
from models.model import QueryRequest
from utils.tools import carregar_prompt, extract_sql_query_from_response, get_relevant_table_info, carregar_exemplos_string, access_guard
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
        # 📦 Cargar el prompt según el nivel de acceso
        if query_request.access_level == "Funcionário":
            print("User with low access connected.")
            check = access_guard(query_request.user_name, query_request.question)
            if check == "ALLOWED":
                template_str = carregar_prompt("prompts/lowAccess_primary.txt")
                input_variables = ["input", "top_k", "table_info", "exemplos_string", "user_name"]
            elif check == "BLOCKED":
                print("❌ Acesso negado por tentativa de acessar dados de outro funcionário ou folha salarial.")
                return None, "BLOCKED"
        else:
            print("User with high access connected.")
            template_str = carregar_prompt("prompts/highAccess_primary.txt")
            input_variables = ["input", "top_k", "table_info", "exemplos_string"]

        # 🧠 Crear prompt dinámicamente según variables necesarias
        prompt = PromptTemplate(
            input_variables=input_variables,
            template=template_str
        )

        # 📤 Armar los inputs para el modelo
        model_input = {
            "input": query_request.question,
            "table_info": table_info,
            "top_k": 20,
            "exemplos_string": exemplos_string
        }

        # 👤 Si es funcionário, incluir el nombre del usuario
        if query_request.access_level == "Funcionário":
            model_input["user_name"] = query_request.user_name

        # 🚀 Ejecutar usando el nuevo pipe
        result = (prompt | llm).invoke(model_input)

        # El nuevo objeto result es un `AIMessage`, así que usamos `.content` directamente
        text_response = result.content

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

