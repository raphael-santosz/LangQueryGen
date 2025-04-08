from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, PromptTemplate

# Inicializando o modelo Ollama
llm = ChatOllama(model="mistral", temperature=0)

# Definindo o prompt do modelo para gerar uma resposta natural
template = """
Você está sendo solicitado a gerar uma resposta natural e clara com base nos dados fornecidos. 
Aqui estão os resultados da consulta que você executou:

{query_results}

Com base nessas informações, por favor, gere uma resposta completa para a pergunta do usuário:
{user_question}

A resposta deve ser completa e natural, como se estivesse explicando os resultados de maneira acessível.
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
        return "Nenhum dado encontrado para a sua pergunta."

    # Formata os resultados da consulta de forma legível
    formatted_results = "\n".join([f"{k}: {v}" for row in query_results for k, v in row.items()])
    
    # Formata as variáveis em uma lista de mensagens (para evitar o erro de tipo de entrada)
    formatted_input = prompt.format_messages(query_results=formatted_results, user_question=user_question)

    # Chama o modelo para gerar uma resposta natural com base nos resultados formatados
    result = llm.invoke(formatted_input)

    # Corrigido para acessar o conteúdo do AIMessage corretamente
    return result.content  # Usando o atributo text da instância AIMessage
