from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import PromptTemplate
from sqlalchemy.sql import text
from utils.tools import extract_sql_query_from_response, get_relevant_table_info,carregar_prompt  # Importando a função de extração
import json
from utils.tools import carregar_exemplos_string
from models.model import QueryRequest

# Exemplos
exemplos_string = carregar_exemplos_string('utils/exemplos.json')

# Configurações do modelo e banco
llm = ChatOllama(model="llama3:8b", temperature=0)
db = SQLDatabase.from_uri("mssql+pyodbc://@RAPHAEL_PC/Teste_RAG?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server")

def validate_and_refine_query(user_question: str, generated_query: str, query_results: list, access_level: str, user_name: str) -> tuple:
    # Captura a estrutura da base de dados dinamicamente
    table_info = get_relevant_table_info(db)
    query = None

    try:
        # 📦 Cargar el prompt según el nivel de acceso
        if access_level == "Funcionário":
            template_str = carregar_prompt("prompts/lowAccess_validate.txt")
            input_variables = ["user_question", "generated_query", "query_results", "table_info", "exemplos_string", "user_name"]
        else:
            template_str = carregar_prompt("prompts/highAccess_validate.txt")
            input_variables = ["user_question", "generated_query", "query_results", "table_info", "exemplos_string"]

        prompt = PromptTemplate(
            input_variables=input_variables,
            template=template_str
        )

        # 📤 Construir inputs
        model_input = {
            "user_question": user_question,
            "generated_query": generated_query,
            "query_results": query_results,
            "table_info": table_info,
            "exemplos_string": exemplos_string
        }

        if access_level == "Funcionário":
            model_input["user_name"] = user_name  # 👤 Añadir nombre del usuario

        # 🚀 Ejecutar el modelo
        result = (prompt | llm).invoke(model_input)
        
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

