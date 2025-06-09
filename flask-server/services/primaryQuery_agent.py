from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from models.model import QueryRequest, QueryResponse
from utils.tools import extract_sql_query_from_response  # Função de extração de SQL
import json
from sqlalchemy import text
from utils.tools import carregar_exemplos_string

# Configuração do banco de dados (se necessário)
database_uri = "mssql+pyodbc://@RAPHAEL_PC/Teste_RAG?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
db = SQLDatabase.from_uri(database_uri)

# Exemplos
exemplos_string = carregar_exemplos_string('utils/exemplos.json')

# Modelo
llm = ChatOllama(model="nous-hermes2", temperature=0)


# Prompt
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
Pay special attention to any similar questions and their corresponding queries.

When generating the query, make sure to follow SQL Server conventions, especially for calculations like FGTS, salary, and date-related operations (e.g., use DATEDIFF, DATEADD, CAST, etc.).

### IMPORTANT
- Return ONLY the SQL query. Do NOT provide any additional explanation or comments.
- Do NOT use columns or tables that are not present in the DATABASE SCHEMA section.
- The output must be ONLY the SQL query, with no leading or trailing text.

"""

prompt = PromptTemplate(
    input_variables=["input", "top_k", "table_info", "exemplos_string"],
    template=template
)

# Cadeia
chain = LLMChain(llm=llm, prompt=prompt)

def generate_sql_query(query_request: QueryRequest) -> QueryResponse:
    print("Entramos na IA1")
    raw_query = None

    try:
        result = chain.invoke({
            "input": query_request.question,
            "table_info": db.get_table_info(),
            "top_k": 20,
            "exemplos_string": exemplos_string  # Passando os exemplos para o modelo
        })

        print("Consulta SQL gerada com sucesso.")
        text_response = result["text"]

        print("Extraindo a consulta SQL da resposta...")
        raw_query = extract_sql_query_from_response(text_response)
        print(f"Consulta extraída: {raw_query}")

        # Executar a consulta no banco de dados
        print("Executando a consulta no banco de dados...")
        with db._engine.connect() as conn:
            result = conn.execute(text(raw_query)).fetchall()
            if isinstance(result, list) and all(hasattr(row, "_mapping") for row in result):
                result_data = [
                    {k: str(v) for k, v in row._mapping.items()}
                    for row in result
                ]
            else:
                result_data = [{"error": "Resultado inválido. A IA retornou algo inesperado."}]

        print("Consulta executada com sucesso no banco de dados.")

        # Retorna tanto a consulta gerada quanto os dados da execução
        return {"query": raw_query, "result_data": result_data}

    except Exception as e:
        print(f"❌ Erro ao executar o processo: {e}")
        # Em vez de retornar uma string no segundo elemento, retorne uma lista com um dicionário de erro
        error_message = "Ocorreu um erro ao tentar processar sua solicitação."
        error_data = [{"error": error_message}]
        return raw_query, error_data