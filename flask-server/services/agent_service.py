from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain.chains import LLMChain
from sqlalchemy import text
from models.model import QueryRequest, QueryResponse
from langchain_core.prompts import PromptTemplate
from services.validation_agent import validate_and_refine_query  # IA2 chamada diretamente
from services.response_executor import generate_answer
from utils.tools import extract_sql_query_from_response  # Função de extração de SQL
import json

# Configuração do banco
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

def run_query_agent(query_request: QueryRequest) -> QueryResponse:
    try:
        print("Iniciando a geração da consulta SQL...")

        result = chain.invoke({
            "input": query_request.question,
            "table_info": db.get_table_info(),
            "top_k": 20,
            "exemplos_string": exemplos_string
        })

        print("Consulta SQL gerada com sucesso.")
        text_response = result["text"]

        print("Extraindo a consulta SQL da resposta...")
        raw_query = extract_sql_query_from_response(text_response)
        print(f"Consulta extraída: {raw_query}")

        print("Executando a consulta no banco de dados...")
        with db._engine.connect() as conn:
            result = conn.execute(text(raw_query)).fetchall()
            result_data = [
                {k: str(v) for k, v in row._mapping.items()}
                for row in result
            ]
        print("Consulta executada com sucesso no banco de dados.")

        print("Passando para a IA2 para validação e refinamento...")
        try:
            refined_query, refined_result_data = validate_and_refine_query(query_request.question, raw_query, result_data)
            print("Consultas refinadas pela IA2.")
        except Exception as e:
            print(f"❌ Erro ao executar o processo na IA2: {e}")
            refined_query, refined_result_data = None, []

        # Geração da resposta com os dados refinados, mas agora controlamos os prints
        if refined_result_data:
            answer = generate_answer(query_request.question, refined_result_data)
        else:
            error_message = "Não foi possível gerar uma resposta devido a falhas no refinamento da consulta ou na execução no banco de dados."
            refined_result_data = [error_message]
            answer = generate_answer(query_request.question, refined_result_data)

        # Imprimir a resposta gerada apenas uma vez, ao final do processo
        print(f"📝 Resposta final gerada pelo modelo: {answer}")

    except Exception as e:
        print(f"❌ Erro ao executar a consulta, enviando para IA2 para validação e refinamento: {e}")
        error_message = str(e)

        try:
            refined_query, refined_result_data = validate_and_refine_query(query_request.question, raw_query, error_message)
            print("Erro refinado pela IA2.")
        except Exception as e:
            print(f"❌ Erro ao executar o processo na IA2: {e}")
            refined_query, refined_result_data = None, []

        # Geração da resposta final em caso de erro
        if refined_result_data:
            answer = generate_answer(query_request.question, refined_result_data)
        else:
            error_message = "Não foi possível gerar uma resposta devido a falhas no refinamento da consulta ou na execução no banco de dados."
            refined_result_data = [error_message]
            answer = generate_answer(query_request.question, refined_result_data)

        print(f"📝 Resposta final gerada pelo modelo: {answer}")

    return {"output": answer}
