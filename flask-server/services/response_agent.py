from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, PromptTemplate
from utils.tools import carregar_guides_md
from langdetect import detect

# Inicializando o modelo Ollama
llm = ChatOllama(model="gemma:7b-instruct", temperature=0)


# Cargando el formatting guide (path relativo)
formatting_guide = carregar_guides_md("utils/formatting_guide.md")
answering_guide = carregar_guides_md("./utils/answering_guide.md")

# Definindo o prompt do modelo para gerar uma resposta natural
template = """
### TASK
You are asked to generate a clear, friendly, and natural response based on the provided query results, ensuring a professional tone and providing clarity for non-technical users.

### USER QUESTION
{user_question}

### QUERY RESULTS
{query_results}

### ANSWERING GUIDE
These examples are written in different languages to show formatting only. YOU MUST ALWAYS answer using the same language as the USER QUESTION above, regardless of the language used in these examples.
{answering_guide}

### FORMATTING GUIDE
{formatting_guide}

### INSTRUCTIONS
- DO NOT repeat or rephrase the USER QUESTION or the QUERY RESULTS in your output. Your output must contain ONLY the RESPONSE part.
- Your output must follow the tone and format of the examples in the ANSWERING GUIDE.
- You must ONLY output the final response text — do not include the USER QUESTION, the QUERY RESULTS, or any labels.
- If QUERY RESULTS contains any error message (such as SQL_ERROR_OCCURRED) or indicates that no data was found (such as NO_RESULTS_FOUND), you MUST respond politely and naturally, following the RESPONSE examples shown in the ANSWERING GUIDE. 

### IMPORTANT
- **Error or No Data**: If QUERY RESULTS is either SQL_ERROR_OCCURRED or NO_RESULTS_FOUND, generate a polite and helpful message just like the RESPONSE examples in the ANSWERING GUIDE. 
- **Response Output**: Your output must ONLY be the RESPONSE text, formatted as shown in the ANSWERING GUIDE. Do NOT include USER QUESTION or QUERY RESULTS sections in your answer.
- **Accuracy**: Only use the information in QUERY RESULTS to answer. Do not assume or invent any extra information.

### LANGUAGE
Respond strictly in this language: {response_language}

### RESPONSE

"""


# Corrigindo a criação do prompt para aceitar um objeto PromptTemplate
prompt = ChatPromptTemplate.from_messages([
    HumanMessagePromptTemplate(
        prompt=PromptTemplate(input_variables=["query_results", "user_question","formatting_guide","answering_guide"], template=template)
    )
])


# Função para formatar os resultados de forma robusta
def format_query_results(query_results):
    if query_results == "SQL_ERROR_OCCURRED":
        return "SQL_ERROR_OCCURRED"

    if query_results == "NO_RESULTS_FOUND":
        return "NO_RESULTS_FOUND"

    # En cualquier otro caso, asumimos que es list[dict]
    formatted_rows = []
    for i, row in enumerate(query_results, 1):
        row_text = " | ".join([f"{k}: {v}" for k, v in row.items()])
        formatted_rows.append(f"Row {i}: {row_text}")

    return "\n".join(formatted_rows)


# Função para gerar resposta natural
def generate_answer(user_question, query_results):
    # Detectar idioma
    lang = detect(user_question)
    lang_map = {'en': 'English', 'es': 'Spanish', 'pt': 'Portuguese'}
    response_language = lang_map.get(lang, 'English')
    print("Language: ",response_language)
    # Formata os resultados da consulta
    formatted_results = format_query_results(query_results)

    # Formata as variáveis em uma lista de mensagens (para evitar o erro de tipo de entrada)
    formatted_input = prompt.format_messages(query_results=formatted_results, user_question=user_question,formatting_guide=formatting_guide,answering_guide=answering_guide,response_language=response_language)

    # Chama o modelo para gerar uma resposta natural com base nos resultados formatados
    result = llm.invoke(formatted_input)

    # Retorna o conteúdo da resposta
    return result.content
