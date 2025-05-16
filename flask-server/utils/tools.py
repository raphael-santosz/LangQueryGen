from langchain.schema import AIMessage
from PyPDF2 import PdfReader
from docx import Document

def extract_sql_query_from_response(result) -> str:
    """
    Função para extrair a query SQL da resposta da IA.
    Se a resposta for um AIMessage, acessa o campo 'content'. 
    Se for uma string simples, apenas aplica o 'strip' para limpar.
    """
    # Verifica se o resultado é uma instância de AIMessage
    if isinstance(result, AIMessage):
        query = result.content.strip()  # Acessa diretamente o conteúdo da mensagem e aplica strip
    else:
        query = result.strip()  # Caso contrário, trata como string simples
    
    if not query:
        raise ValueError("❌ A resposta da IA não contém uma query SQL válida.")
    
    return query

def extract_text_from_pdf(pdf_path: str) -> str:
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
    return text

def extract_text_from_word(docx_path: str) -> str:
    doc = Document(docx_path)
    text = ''
    for paragraph in doc.paragraphs:
        text += paragraph.text + '\n'
    return text

def extract_text_from_file(file_path: str) -> str:
    if file_path.endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith('.docx'):
        return extract_text_from_word(file_path)
    else:
        raise ValueError("Formato de arquivo não suportado.")
    
import json
from pathlib import Path

def carregar_exemplos_string(caminho_exemplos: str = None) -> str:
    """
    Lê o arquivo JSON de exemplos e formata a string para uso nos prompts.
    :param caminho_exemplos: caminho para o arquivo JSON de exemplos. 
                             Se None, usa o caminho padrão './utils/exemplos.json'
    :return: string formatada com exemplos prontos para injeção em prompts.
    """
    if caminho_exemplos is None:
        # Caminho padrão relativo à raiz do projeto
        caminho_exemplos = Path(__file__).parent.parent / 'utils' / 'exemplos.json'
    else:
        caminho_exemplos = Path(caminho_exemplos)

    try:
        with open(caminho_exemplos, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            exemplos = dados.get("exemplos", [])
    except Exception as e:
        print(f"Erro ao carregar exemplos JSON: {e}")
        return ""

    # Formata a lista de exemplos no padrão esperado
    exemplos_string = "\n".join([f"- {exemplo['pergunta']} => {exemplo['query']}" for exemplo in exemplos])
    return exemplos_string
