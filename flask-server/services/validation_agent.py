from langchain_ollama import ChatOllama 
from langchain_community.utilities import SQLDatabase
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from sqlalchemy.sql import text
from utils.tools import extract_sql_query_from_response  # Função de extração de SQL
import json

# Configurações do modelo e banco
llm = ChatOllama(model="mistral", temperature=0)
db = SQLDatabase.from_uri("mssql+pyodbc://@RAPHAEL_PC/Teste_RAG?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server")

# Exemplos
caminho_exemplos = './utils/exemplos.json'

# Carregando os exemplos de queries de um arquivo JSON
with open(caminho_exemplos, 'r') as file:
    exemplos = json.load(file)["exemplos"]

# Formatar os exemplos como uma lista de strings
exemplos_string = "\n".join([f"- {exemplo['pergunta']} => {exemplo['query']}" for exemplo in exemplos])

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

# Criando o prompt a partir do template
prompt = PromptTemplate(
    input_variables=["input", "top_k", "table_info", "exemplos_string"],
    template=template
)

# Cadeia
chain = LLMChain(llm=llm, prompt=prompt)

def validate_and_refine_query(user_question: str, generated_query: str, query_results: list) -> str:
    """
    Recebe a pergunta do usuário e a query gerada pela IA1. Verifica se a query é adequada
    e a refina se necessário, retornando uma nova query refinada.
    """
    # Formatação do prompt
    formatted_prompt = prompt.format(
        input=user_question, 
        top_k=20,  # Ajuste conforme necessário
        table_info=db.get_table_info(),
        exemplos_string=exemplos_string
    )
    
    try:
        # Chama o modelo para executar a query gerada ou ajustada
        result = llm.invoke(formatted_prompt)
        
        # Extração da query SQL da resposta
        query = extract_sql_query_from_response(result)
        
        # Executando a consulta no banco de dados
        with db._engine.connect() as conn:
            result = conn.execute(text(query)).fetchall()
            refined_result_data = [
                {k: str(v) for k, v in row._mapping.items()}
                for row in result
            ]
            
            # Se não houver resultados, passamos a mensagem para a IA3
            if not refined_result_data:
                return "Não foi possível encontrar dados relacionados à sua pergunta."

            return query, refined_result_data  # Retorna a query gerada e os dados encontrados no banco
        
    except Exception as e:
        print(f"❌ Erro ao executar o processo: {e}")
        return "Ocorreu um erro ao tentar processar sua solicitação."
