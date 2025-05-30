from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain.chains import LLMChain
from sqlalchemy import text
from models.model import QueryRequest, QueryResponse
from langchain_core.prompts import PromptTemplate
from services.validation_agent import validate_and_refine_query  # IA2 chamada diretamente
from services.response_executor import generate_answer
from services.ai1 import generate_sql_query
from utils.tools import extract_sql_query_from_response  # Função de extração de SQL
import json


def run_query_agent(query_request: QueryRequest) -> QueryResponse:
    try:
        print("Iniciando a geração da consulta SQL...")

        raw_query, result_data = generate_sql_query(query_request)

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
