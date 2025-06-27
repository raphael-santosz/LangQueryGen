from flask import Blueprint, request, jsonify
from services.agent_service import run_query_agent
from models.model import QueryRequest
import os
from utils.tools import decrypt_token

api_bp = Blueprint("api", __name__)

# Diretório para armazenar os arquivos enviados
UPLOAD_FOLDER = 'uploads/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@api_bp.route("/generate-query", methods=["POST"])
def generate_query():
    try:
        # Captura a mensagem e o token enviados
        question = request.form.get('question')
        token = request.form.get('token')

        access_level, user_name = decrypt_token(token)

        # Verifica se foi enviado um arquivo
        file = request.files.get('file')
        file_url = None

        if file:
            # Se o arquivo foi enviado, imprime informações sobre o arquivo
            print(f"Arquivo recebido: {file.filename}")
            filename = file.filename
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            file_url = file_path
            print(f"Arquivo salvo em: {file_path}")
        else:
            print("Nenhum arquivo recebido.")
        
        # Criar o objeto QueryRequest com a mensagem, o arquivo (file_url) e o token
        query_request = QueryRequest(question=question, file_url=file_url, access_level=access_level, user_name=user_name)
        print(f"Objeto QueryRequest criado: {query_request}")

        # Passando para a IA para gerar a resposta
        response = run_query_agent(query_request)

        # Retornar a resposta
        print("Resposta retornada ao frontend")
        return jsonify(response)  # já retorna {"output": ...}
    
    except Exception as e:
        print(f"Erro na API: {e}")
        return jsonify({"error": str(e)}), 500
