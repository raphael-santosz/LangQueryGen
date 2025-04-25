from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain.chains import LLMChain
from sqlalchemy import text
from utils.tools import fix_capitalization_dynamic
from models.model import QueryRequest, QueryResponse
from langchain_core.prompts import PromptTemplate
from services.response_executor import generate_answer


# Configuração do banco
database_uri = "mssql+pyodbc://@RAPHAEL_PC/Teste_RAG?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
db = SQLDatabase.from_uri(database_uri)

# Modelo
llm = ChatOllama(model="mistral", temperature=0)

# Prompt
template = """Given an input question, generate a syntactically correct SQL query.
Use the following table info: {table_info}
Consider at most {top_k} relevant tables.
Question: {input}

Respond only with the SQL query prefixed by 'SQL query:' and nothing else.
"""
prompt = PromptTemplate(
    input_variables=["input", "top_k", "table_info"],
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
            "top_k": 20
        })

        text_response = result["text"]
        # Log específico da IA
        print(f"📦 Resposta completa do modelo: {text_response}")

        # Extração da query SQL da resposta
        sql_start = text_response.find("SQL query:")
        if sql_start != -1:
            raw_query = text_response[sql_start + len("SQL query:"):].strip()
        else:
            raise ValueError("❌ Prefixo 'SQL query:' não encontrado na resposta do modelo.")

        # Log da query extraída
        print(f"🧠 Raw query extraída: {raw_query}")

        # Execução da consulta no banco de dados
        with db._engine.connect() as conn:
            result = conn.execute(text(raw_query)).fetchall()
            result_data = [
                {k: str(v) for k, v in row._mapping.items()}
                for row in result
            ]
            print(f"📊 Resultados da query: {result_data}")
        
        # Se a execução da consulta for bem-sucedida, passamos a consulta e o resultado para a IA2
        validation_result = validation_agent_executor.invoke({
            "user_question": query_request.question,
            "generated_query": raw_query,
            "query_result": result_data  # Passando o resultado para a IA2
        })
        print(f"🔧 Query refinada pela IA2: {validation_result}")

    except Exception as e:
        print(f"❌ Erro ao executar a consulta, enviando para IA2 para validação e refinamento: {e}")
        # Se houve erro, passamos a consulta, o erro e o resultado para a IA2
        error_message = str(e)  # Capturando o erro como uma string para enviar à IA2
        
        validation_result = validation_agent_executor.invoke({
            "user_question": query_request.question,
            "generated_query": raw_query,
            "query_result": error_message  # Passando o erro para ajudar a IA2
        })
        print(f"🔧 Query refinada pela IA2 após erro: {validation_result}")
    
    # Agora, após a IA2 refinar a query, chamamos a IA3 para gerar a resposta natural
    answer = generate_answer(query_request.question, result_data)
    print(f"📝 Resposta gerada pelo modelo: {answer}")

    return {"output": answer}
