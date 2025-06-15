from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from models.model import QueryRequest
from utils.tools import carregar_prompt, extract_text_from_file

# Configuração do modelo
llm = ChatOllama(model="llama3:8b", temperature=0)

# Função para analisar documentos e buscar a resposta
def analyze_document(query_request: QueryRequest):
    print("Entramos na IA4 (Document Reader)")

    try:
        # 📄 Extrair texto do documento
        if not query_request.file_url:
            print("⚠️ Nenhum documento fornecido.")
            return ""

        extracted_text = extract_text_from_file(query_request.file_url)

        if not extracted_text.strip():
            print("⚠️ Texto extraído vazio ou inválido.")
            return ""

        # 🧠 Preparar prompt
        template_str = carregar_prompt("prompts/document_reader.txt")

        prompt = PromptTemplate(
            input_variables=["input", "text_document"],
            template=template_str
        )

        model_input = {
            "input": query_request.question,
            "text_document": extracted_text
        }

        # 🚀 Executar prompt com modelo
        result = (prompt | llm).invoke(model_input)
        document_answer = result.content.strip()
        print("Respuesta del modelo document: ", document_answer)

        normalized_answer = document_answer.strip().upper().replace("*", "")
        if normalized_answer == "NO_RELEVANT_DATA_FOUND":
            print("⚠️ Documento no contiene información relevante.")
            return "NO_DOCUMENT_DATA"
        elif normalized_answer:
            print("✅ Documento contiene una posible respuesta.")
            return normalized_answer
        else:
            print("⚠️ Documento retornou uma resposta vazia.")
            return "NO_DOCUMENT_DATA"

    except Exception as e:
        print(f"❌ Erro na IA4 ao analisar documento: {e}")
        return ""
