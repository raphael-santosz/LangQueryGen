from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from models.model import QueryRequest, QueryResponse
from utils.tools import extract_sql_query_from_response  # Função de extração de SQL
import json
from sqlalchemy import text

# Configuração do banco de dados (se necessário)
database_uri = "mssql+pyodbc://@RAPHAEL_PC/Teste_RAG?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
db = SQLDatabase.from_uri(database_uri)

# Exemplos
caminho_exemplos = './utils/exemplos.json'

# Carregando os exemplos de queries de um arquivo JSON
with open(caminho_exemplos, 'r') as file:
    exemplos = json.load(file)["exemplos"]

# Formatar os exemplos como uma lista de strings
exemplos_string = "\n".join([f"- {exemplo['pergunta']} => {exemplo['query']}" for exemplo in exemplos])

# Modelo
llm = ChatOllama(model="mistral", temperature=0)

# Prompt
template = """Given an input question, generate a syntactically correct SQL query for SQL Server.
Use the following table info: {table_info}
Consider at most {top_k} relevant tables.
Question: {input}
Examples to base your queries: 
{exemplos_string}

Before generating the query, carefully review the provided examples to ensure the query matches the patterns in these examples. Pay special attention to any similar questions and their corresponding queries.

When generating the query, make sure to follow SQL Server conventions, especially for calculations like FGTS, salary, and date-related operations (e.g., use DATEDIFF, DATEADD, CAST, etc.).

Respond only with the SQL query without any additional explanation.
"""

prompt = PromptTemplate(
    input_variables=["input", "top_k", "table_info", "exemplos_string"],
    template=template
)

# Cadeia
chain = LLMChain(llm=llm, prompt=prompt)

def generate_sql_query(query_request: QueryRequest) -> QueryResponse:
    print("Entramos na IA1")

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
            result_data = [
                {k: str(v) for k, v in row._mapping.items()}
                for row in result
            ]
        print("Consulta executada com sucesso no banco de dados.")

        # Retorna tanto a consulta gerada quanto os dados da execução
        return {"query": raw_query, "result_data": result_data}

    except Exception as e:
        print(f"❌ Erro ao gerar a consulta SQL na IA1: {e}")
        raise Exception("Erro ao gerar a consulta SQL na IA1.")
