from langchain.schema import AIMessage
from PyPDF2 import PdfReader
from docx import Document
import re
import json
from pathlib import Path
from sqlalchemy import inspect, text
from langchain_community.utilities import SQLDatabase
from sqlalchemy import inspect
import concurrent.futures


import re
from langchain_core.messages import AIMessage

import re
from langchain_core.messages import AIMessage

def extract_sql_query_from_response(result) -> str:
    """
    Extrae la última instrucción SELECT válida de la respuesta de la IA.
    Elimina posibles comentarios y explicaciones previas, y descarta instrucciones peligrosas.
    """

    # Extraer el contenido de texto
    content = result.content.strip() if isinstance(result, AIMessage) else str(result).strip()

    # Buscar todas las ocurrencias de SELECT
    matches = list(re.finditer(r'\bSELECT\b', content, re.IGNORECASE))
    if not matches:
        raise ValueError("❌ No se encontró una instrucción SELECT válida en la respuesta de la IA.")

    # Tomar la última aparición
    last_match = matches[-1]
    query = content[last_match.start():].strip()

    # Opcional: quitar bloques markdown
    if query.startswith("```sql"):
        query = query[6:]  # quitar ```sql
    query = query.strip("` \n")

    # Validación básica
    if not query.upper().startswith("SELECT"):
        raise ValueError("❌ La query extraída no comienza con SELECT. Posible contenido inválido.")

    # Asegurar que no contiene comandos peligrosos
    forbidden = ['UPDATE', 'DELETE', 'INSERT', 'DROP', 'ALTER']
    if any(cmd in query.upper() for cmd in forbidden):
        raise ValueError("❌ La respuesta contiene comandos peligrosos.")

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
    
def carregar_exemplos_string(caminho_exemplos: str = None) -> str:
    """
    Lê o arquivo JSON de exemplos e formata a string para uso nos prompts.
    Suporta o novo formato com 'perguntas': [ ... ] e 'query': ...
    
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

    # Formata a lista de exemplos no padrão esperado (para cada pergunta do array)
    exemplos_string = "\n".join([
        f"- {pergunta} => {exemplo['query']}"
        for exemplo in exemplos
        for pergunta in exemplo.get("perguntas", [])
    ])
    
    return exemplos_string

def carregar_guides_md(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def get_table_example(db, table):
    """
    Obtiene el ejemplo de datos de la tabla especificada.
    """
    # Inspeccionar las columnas de la tabla
    inspector = inspect(db._engine)
    columns = [column['name'] for column in inspector.get_columns(table)]
    query = f"SELECT TOP 2 {', '.join(columns)} FROM {table}"

    try:
        # Ejecutar la consulta
        with db._engine.connect() as conn:
            result = conn.execute(text(query)).fetchall()

        # Formatear filas
        example_rows = [{columns[i]: row[i] for i in range(len(columns))} for row in result]

        return {table: {"columns": columns, "example_rows": example_rows}}

    except Exception as e:
        print(f"❌ Error al obtener datos de la tabla {table}: {e}")
        return {table: {"columns": columns, "example_rows": []}}

def get_relevant_table_info(db: SQLDatabase) -> dict:
    """
    Obtiene la información relevante de las tablas utilizando concurrencia.
    """
    table_info = {}

    # Inspeccionar las tablas del esquema
    inspector = inspect(db._engine)
    tables = inspector.get_table_names()

    # Usar concurrencia para ejecutar las consultas de las tablas en paralelo
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(get_table_example, db, table): table for table in tables}
        
        for future in concurrent.futures.as_completed(futures):
            table = futures[future]
            try:
                table_info.update(future.result())
            except Exception as e:
                print(f"Error al procesar la tabla {table}: {e}")
    
    return table_info
