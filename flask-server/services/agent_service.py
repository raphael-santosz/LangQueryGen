from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain.chains import LLMChain
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from sqlalchemy import text
from utils.tools import fix_capitalization_dynamic, log_agent_response
from models.model import QueryRequest, QueryResponse
from langchain_core.prompts import PromptTemplate
import os

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

# Função principal
def run_query_agent(query_request: QueryRequest) -> QueryResponse:
    print("📩 Recebida pergunta:", query_request.question)

    try:
        result = chain.invoke({
            "input": query_request.question,
            "table_info": db.get_table_info(),
            "top_k": 20
        })

        text_response = result["text"]
        print("📦 Resposta completa do modelo:", text_response)

        sql_start = text_response.find("SQL query:")
        if sql_start != -1:
            raw_query = text_response[sql_start + len("SQL query:"):].strip()
        else:
            raise ValueError("❌ Prefixo 'SQL query:' não encontrado na resposta do modelo.")

        print("🧠 Raw query extraída:", raw_query)

    except Exception as e:
        print("❌ Erro ao gerar raw query:", e)
        raise

    try:
        fixed_query = fix_capitalization_dynamic(raw_query)
        print("🧼 Fixed query:", fixed_query)
    except Exception as e:
        print("❌ Erro ao aplicar fix_capitalization_dynamic:", e)
        raise

    try:
        with db._engine.connect() as conn:
            result = conn.execute(text(fixed_query)).fetchall()
            result_data = [
            {k: str(v) for k, v in row._mapping.items()}
            for row in result]
            print("📊 Resultados da query:", result_data)
    except Exception as e:
        print("❌ Erro ao executar a query:", e)
        raise

    log_agent_response(query_request.question, raw_query, fixed_query, result_data)

    return {"output": text_response}

