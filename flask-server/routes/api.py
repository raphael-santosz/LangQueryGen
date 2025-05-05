from flask import Blueprint, request, jsonify
from services.agent_service import run_query_agent
from models.model import QueryRequest, QueryResponse

api_bp = Blueprint("api", __name__)

@api_bp.route("/generate-query", methods=["POST"])
def generate_query():
    try:
        data = request.get_json()
        query_request = QueryRequest(**data)
        response = run_query_agent(query_request)
        return jsonify(response)  # já retorna {"output": ...}
    except Exception as e:
        return jsonify({"error": str(e)}), 500

