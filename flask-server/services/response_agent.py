from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, PromptTemplate

# Inicializando o modelo Ollama
llm = ChatOllama(model="openchat", temperature=0)

# Definindo o prompt do modelo para gerar uma resposta natural
template = """
### TASK
You are asked to generate a natural and clear response based on the provided query results.

### QUERY RESULTS
{query_results}

### USER QUESTION
{user_question}

### INSTRUCTIONS
- Generate a complete and natural response as if you are explaining the results to a non-technical user who does not understand SQL.
- The response must be written in the same language as the user question (Portuguese if in Portuguese, Spanish if in Spanish, English if in English).
- Do NOT include any SQL code or SQL explanations. Just provide the natural language answer.
- If the query results are empty, explain politely that no data was found.

### RESPONSE
"""


# Corrigindo a criação do prompt para aceitar um objeto PromptTemplate
prompt = ChatPromptTemplate.from_messages([
    HumanMessagePromptTemplate(
        prompt=PromptTemplate(input_variables=["query_results", "user_question"], template=template)
    )
])

def generate_answer(user_question, query_results):
    # Verifica se os resultados estão vazios
    if not query_results:
        return "Desculpe, não encontramos resultados para a sua pergunta."

    # Formata os resultados da consulta de forma legível
    formatted_results = "\n".join([f"{k}: {v}" for row in query_results for k, v in row.items()])
    
    # Formata as variáveis em uma lista de mensagens (para evitar o erro de tipo de entrada)
    formatted_input = prompt.format_messages(query_results=formatted_results, user_question=user_question)

    # Chama o modelo para gerar uma resposta natural com base nos resultados formatados
    result = llm.invoke(formatted_input)

    # Corrigido para acessar o conteúdo do AIMessage corretamente
    return result.content  # Usando o atributo text da instância AIMessage
