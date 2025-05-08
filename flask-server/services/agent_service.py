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
        # Geração da consulta SQL com base na pergunta
        result = chain.invoke({
            "input": query_request.question,
            "table_info": db.get_table_info(),
            "top_k": 20,
            "exemplos_string": exemplos_string  # Passando os exemplos para o modelo
        })

        text_response = result["text"]

        # Extração da query SQL da resposta usando a função nova
        raw_query = extract_sql_query_from_response(text_response)

        # Execução da consulta no banco de dados
        with db._engine.connect() as conn:
            result = conn.execute(text(raw_query)).fetchall()
            result_data = [
                {k: str(v) for k, v in row._mapping.items()}
                for row in result
            ]
        
        # Passando para IA2 com a função de validação e refinamento
        try:
            refined_query, refined_result_data = validate_and_refine_query(query_request.question, raw_query, result_data)
        except Exception as e:
            print(f"❌ Erro ao executar o processo na IA2: {e}")
            # Caso a IA2 falhe, envia a mensagem de erro de forma mais clara
            refined_query, refined_result_data = None, []
            # Geração da resposta natural baseada nos resultados da consulta refinada ou original
        answer = generate_answer(query_request.question, refined_result_data)
        print(f"📝 Resposta gerada pelo modelo: {answer}")

    except Exception as e:
        print(f"❌ Erro ao executar a consulta, enviando para IA2 para validação e refinamento: {e}")
        # Se houve erro, passamos a consulta, o erro e o resultado para a IA2
        error_message = str(e)  # Capturando o erro como uma string para enviar à IA2

        try:
            refined_query, refined_result_data = validate_and_refine_query(query_request.question, raw_query, error_message)
        except Exception as e:
            print(f"❌ Erro ao executar o processo na IA2: {e}")
            # Caso a IA2 falhe, envia a mensagem de erro de forma mais clara
            refined_query, refined_result_data = None, []
    
        # Agora, após a IA2 refinar a query, chamamos a IA3 para gerar a resposta natural
    if refined_result_data:  # Se a IA2 conseguiu refinar a query corretamente
        answer = generate_answer(query_request.question, refined_result_data)
    else:  # Caso contrário, passamos a mensagem de erro que a IA2 falhou
        # Mensagem informando que a consulta não pôde ser processada
        error_message = "Não foi possível gerar uma resposta devido a falhas no refinamento da consulta ou na execução no banco de dados."
        
        # Passando a mensagem de erro para a IA3 refinar a resposta
        refined_result_data = [error_message]  # Em vez de deixar vazio, definimos uma mensagem clara
        
        # Gerando a resposta com a mensagem de erro
        answer = generate_answer(query_request.question, refined_result_data)

    print(f"📝 Resposta gerada pelo modelo: {answer}")

    return {"output": answer}
