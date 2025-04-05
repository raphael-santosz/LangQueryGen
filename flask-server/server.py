from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import nacl.secret
import nacl.utils
from nacl.encoding import Base64Encoder
from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotPromptTemplate,
    PromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import SystemMessage
import re
import time
from sqlalchemy import text
from langchain.agents import initialize_agent, AgentType, Tool
from langchain_community.tools.sql_database.tool import (
    QuerySQLDataBaseTool,
    InfoSQLDatabaseTool,
    ListSQLDatabaseTool
)

app = Flask(__name__)
CORS(app)

database_uri = "mssql+pyodbc://@RAPHAEL_PC/Teste_RAG?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
sql_db = SQLDatabase.from_uri(database_uri)
# 🔍 Teste se o banco contém dados
with sql_db._engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM Funcionario"))
    print(f"Total de funcionários no banco: {result.scalar()}")

llm = ChatOllama(model="mistral:7b", base_url="http://localhost:11434", temperature=0, max_tokens=100)  # Limite de tokens

TABLE_INFO = sql_db.get_table_info()  # Cache do esquema

promptValid = ChatPromptTemplate.from_messages([
    ("system", "Você é um agente inteligente que verifica se uma frase se relaciona com salário, pagamentos, dinheiro, raça, religião ou orientação sexual. "
               "Retorne apenas 'Bloqueado' se houver relação, ou 'Permitido' caso contrário."),
    ("user", "{input}"),
])
valid_chain = promptValid | llm

# Exemplo de perguntas e consultas SQL
examples = [
    {
        "input": "Quanto é o saldo de salário do Usuário1?",
        "query": "SELECT (Salario / 30.0) * DATEDIFF(day, DATEFROMPARTS(YEAR(DataDemissao), MONTH(DataDemissao), 1), DataDemissao) AS SaldoSalario FROM Funcionario WHERE Nome = 'Usuário1'"
    },
    {
        "input": "Qual o valor do décimo terceiro proporcional do funcionário Carlos Almeida?",
        "query": "SELECT (Salario / 12.0) * DATEDIFF(month, DATEFROMPARTS(YEAR(GETDATE()), 1, 1), GETDATE()) AS DecimoTerceiro FROM Funcionario WHERE Nome = 'Carlos Almeida'"
    },
    {
        "input": "Qual o valor do FGTS total do funcionário João Gomes?",
        "query": "SELECT (Salario * 0.08) * DATEDIFF(month, DataAdmissao, GETDATE()) AS FGTS FROM Funcionario WHERE Nome = 'João Gomes'"
    },
    {
        "input": "Qual o valor da multa de 40% do FGTS do funcionário João Gomes?",
        "query": "SELECT 0.4 * (Salario * 0.08) * DATEDIFF(month, DataAdmissao, GETDATE()) AS MultaFGTS FROM Funcionario WHERE Nome = 'João Gomes'"
    },
    {
        "input": "Qual o valor da folha de pagamento total da empresa?",
        "query": "SELECT SUM(Salario) AS FolhaPagamento FROM Funcionario WHERE DataDemissao IS NULL"
    },
    {
        "input": "Qual a política de férias da empresa?",
        "query": "SELECT PoliticaDescricao AS Politica FROM Politicas WHERE PoliticaNome LIKE '%Ferias%'"
    },
    {
        "input": "Qual o salário do funcionário João?",
        "query": "SELECT Salario FROM Funcionario WHERE Nome = 'João'"
    },
    {
        "input": "Qual o salário do funcionário Carlos Almeida?",
        "query": "SELECT Salario FROM Funcionario WHERE Nome = 'Carlos Almeida'"
    },
    {
        "input": "Há quantos meses o funcionário Carlos Almeida trabalha na empresa?",
        "query": "SELECT DATEDIFF(month, DataAdmissao, GETDATE()) AS MesesTrabalhados FROM Funcionario WHERE Nome = 'Carlos Almeida'"
    },
    {
        "input": "Qual a média salarial dos funcionários?",
        "query": "SELECT AVG(Salario) AS MediaSalarial FROM Funcionario"
    },
    {
        "input": "Quantos funcionários estão ativos?",
        "query": "SELECT COUNT(*) AS TotalAtivos FROM Funcionario WHERE DataDemissao IS NULL"
    }
]

# Carregar embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
example_selector = SemanticSimilarityExampleSelector.from_examples(examples, embeddings, FAISS, k=2, input_keys=["input"])

system_prefix = """Você é um agente desenvolvido para interagir com uma base de dados SQL.
Aqui está o esquema do banco de dados disponível:
{table_info}

Através de uma pergunta feita num input, crie uma query SQL SERVER sintaticamente correta para executar.
Use SOMENTE as colunas e tabelas listadas em {table_info}. Retorne APENAS a query SQL, sem explicações, raciocínio ou texto adicional, dentro de delimitadores ```sql ... ```.

Se a pergunta não especificar a quantidade de exemplos de retorno, limite sua query a no máximo {top_k} resultados.
Você pode ordenar por colunas relevantes para tornar a resposta mais útil.
Nunca use SELECT *, só as colunas relevantes.
Use DATEDIFF ao trabalhar com datas.
Nunca traduza os nomes das colunas. Use **exatamente** como estão no schema.
Se a pergunta não for sobre a base, responda "Eu não sei".

Aqui estão alguns exemplos de perguntas e queries correspondentes:
"""

few_shot_prompt = FewShotPromptTemplate(
    example_selector=example_selector,
    example_prompt=PromptTemplate.from_template("User input: {input}\nSQL query: {query}"),
    input_variables=["input", "top_k", "table_info"],
    prefix=system_prefix,
    suffix="",
)

full_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate(prompt=few_shot_prompt),
    ("human", "{input}"),
])

sql_chain = create_sql_query_chain(llm, sql_db, prompt=full_prompt)

@app.route("/members")
def members():
    return {"members": ["member1", "member2", "member3"]}

@app.route("/cryptokey")
def retornaChave():
    chave = {'chave': 'q9egeDk+L1t2C8pgH/9rzE/ezPflr3cx6JLujZSiaX8='}
    return jsonify({'chave': chave})

@app.after_request
def remove_server_header(response):
    response.headers.pop('Server', None)
    return response

@app.route('/api/dados', methods=['POST'])
def receber_dados():
    dados = request.json
    print(dados)

    nome = dados.get('nome')
    print(nome)

    token = dados.get('token')
    print(token)

    keyFront = Base64Encoder.decode('q9egeDk+L1t2C8pgH/9rzE/ezPflr3cx6JLujZSiaX8=')  # Chave de criptografia
    encrypted_message_base64 = token
    encrypted_message = Base64Encoder.decode(encrypted_message_base64)

    nonce = encrypted_message[:nacl.secret.SecretBox.NONCE_SIZE]
    encrypted = encrypted_message[nacl.secret.SecretBox.NONCE_SIZE:]

    box = nacl.secret.SecretBox(keyFront)
    start_time = time.time()
    decrypted_message = box.decrypt(encrypted, nonce)
    print(f"Tempo de descriptografia: {time.time() - start_time:.2f} segundos")

    start_time = time.time()
    resultadoValidacao = valid_chain.invoke({"input": nome})
    validacao = resultadoValidacao.content.strip()
    print(f"Tempo de validação: {time.time() - start_time:.2f} segundos")

    if decrypted_message.decode() == 'funcionario':
        if validacao == 'Bloqueado':
            result = {'output': 'Não posso fornecer essa informação.'}
        else:
            start_time = time.time()
            raw_output = sql_chain.invoke({"question": nome, "top_k": 5, "table_info": TABLE_INFO})
            print(f"Tempo de geração da query: {time.time() - start_time:.2f} segundos")

            query_match = re.search(r'```sql\s*(.*?)\s*```', raw_output, re.DOTALL)
            if query_match:
                query = query_match.group(1).strip()
            else:
                query = raw_output.strip()
            print(f"Query gerada: {query}")

            # Verifica a capitalização correta conforme o banco
            query = fix_capitalization_dynamic(query, TABLE_INFO)

            start_time = time.time()
            try:
                result_db = sql_db.run(query)
                result = {'output': result_db}
            except Exception as e:
                result = {'output': f"Erro ao executar a query: {str(e)}"}
            print(f"Tempo de execução da query: {time.time() - start_time:.2f} segundos")
    else:
        start_time = time.time()
        raw_output = sql_chain.invoke({"question": nome, "top_k": 5, "table_info": TABLE_INFO})
        print(f"Tempo de geração da query: {time.time() - start_time:.2f} segundos")

        query_match = re.search(r'```sql\s*(.*?)\s*```', raw_output, re.DOTALL)
        if query_match:
            query = query_match.group(1).strip()
        else:
            query = raw_output.strip()
        print(f"Query gerada: {query}")

        # Verifica a capitalização correta conforme o banco
        query = fix_capitalization_dynamic(query, TABLE_INFO)

        start_time = time.time()
        try:
            result_db = sql_db.run(query)
            result = {'output': result_db}
        except Exception as e:
            result = {'output': f"Erro ao executar a query: {str(e)}"}
        print(f"Tempo de execução da query: {time.time() - start_time:.2f} segundos")

    print(result)
    response = make_response(jsonify({'result': result}))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none';"
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

def fix_capitalization_dynamic(query, table_info):
    """
    Função que ajusta dinamicamente a capitalização da query para coincidir com a estrutura do banco de dados.
    :param query: A query SQL gerada.
    :param table_info: O esquema das tabelas do banco de dados.
    :return: A query com os nomes das tabelas e colunas ajustados.
    """
    # Extração dos nomes das tabelas e colunas do esquema
    table_names = [table['name'] for table in table_info]  # Obtém todas as tabelas
    column_names = {}
    for table in table_info:
        # Cria um dicionário com o nome da tabela e suas respectivas colunas
        column_names[table['name']] = [column['name'] for column in table['columns']]

    # Para cada tabela na query, ajustamos a capitalização
    for table in table_names:
        # Ajuste a tabela de acordo com o que está no banco (se necessário)
        query = query.replace(table.lower(), table)  # Faz a substituição respeitando a capitalização

    # Para cada tabela, ajustamos as colunas
    for table, columns in column_names.items():
        for column in columns:
            # Ajusta a capitalização de cada coluna
            query = query.replace(column.lower(), column)

    return query


tools = [
    Tool(
        name="Schema Info",
        func=InfoSQLDatabaseTool(db=sql_db),
        description="Usado para entender a estrutura do banco de dados"
    ),
    Tool(
        name="List Tables",
        func=ListSQLDatabaseTool(db=sql_db),
        description="Lista todas as tabelas do banco de dados"
    ),
    Tool(
        name="Query Checker",
        func=QuerySQLDataBaseTool(db=sql_db),
        description="Executa queries SQL. Use só após montar a query final."
    )
]

react_agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True
)

if __name__ == "__main__":
    app.run(debug=True)
