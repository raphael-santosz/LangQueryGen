from models.model import QueryRequest
from services.primaryQuery_agent import generate_sql_query  # IA1
from services.validateQuery_agent import validate_and_refine_query  # IA2
from services.response_agent import generate_answer  # IA3
from services.documentSearcher_agent import analyze_document  # IA4
import concurrent.futures


def run_query_agent(query_request: QueryRequest):
    try:
        print("Iniciando a geração da consulta SQL e análise do documento...")

        # Caso 1: Somente pergunta (sem documento)
        if query_request.question and not query_request.file_url:
            print("⚙️ Executando IA1, IA2 e IA3 (sem documento)")
            raw_query, result_data = generate_sql_query(query_request)

            refined_query, refined_result_data = validate_and_refine_query(
                query_request.question, raw_query, result_data,
                query_request.access_level, query_request.user_name
            )

            if refined_result_data:
                answer = generate_answer(query_request.question, refined_result_data, "")
            else:
                error_message = "Não foi possível gerar uma resposta válida."
                answer = generate_answer(query_request.question, [error_message], "")

        # Caso 2: Somente documento (sem pergunta)
        elif query_request.file_url and not query_request.question:
            print("⚠️ Documento fornecido sem pergunta. Ignorando.")
            answer = "No question was submitted. Please send a question along with the document."

        # Caso 3: Pergunta + Documento
        elif query_request.question and query_request.file_url:
            print("⚙️ Executando IA1 + IA4 em paralelo, depois IA2 e IA3")

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_sql = executor.submit(generate_sql_query, query_request)
                future_doc = executor.submit(analyze_document, query_request)

                raw_query, result_data = future_sql.result()
                document_answer = future_doc.result()

            # IA2: validação apenas da query gerada
            refined_query, refined_result_data = validate_and_refine_query(
                query_request.question, raw_query, result_data,
                query_request.access_level, query_request.user_name
            )

            # IA3: Decide entre dados da query e resposta do documento
            answer = generate_answer(
                query_request.question,
                refined_result_data,
                document_answer
            )


        else:
            print("⚠️ Nenhuma entrada válida encontrada.")
            answer = "Entrada inválida: nenhum dado fornecido."

        print(f"📝 Resposta final gerada pelo modelo: {answer}")
        return {"output": answer}

    except Exception as e:
        print(f"❌ Erro inesperado durante o processo: {e}")
        return {"output": "Erro interno ao gerar a resposta."}
