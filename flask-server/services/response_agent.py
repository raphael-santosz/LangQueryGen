from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, PromptTemplate
from utils.tools import carregar_guides_md, carregar_prompt, format_query_results
from langdetect import detect

# Inicializando o modelo Ollama
llm = ChatOllama(model="gemma:7b-instruct", temperature=0)

# Carregando os guias
formatting_guide = carregar_guides_md("utils/formatting_guide.md")
answering_guide = carregar_guides_md("utils/answering_guide.md")


# Carregando o template do prompt principal
template = carregar_prompt("prompts/user_chatbot.txt")

prompt = ChatPromptTemplate.from_messages([
    HumanMessagePromptTemplate(
        prompt=PromptTemplate(
            input_variables=[
                "user_question",
                "query_results",
                "document_results",
                "formatting_guide",
                "answering_guide",
                "response_language"
            ],
            template=template
        )
    )
])
   

# Função principal
def generate_answer(user_question, query_data, document_data):
    lang = detect(user_question)
    lang_map = {'en': 'English', 'es': 'Spanish', 'pt': 'Portuguese'}
    response_language = lang_map.get(lang, 'English')
    print("Language:", response_language)

    has_query = query_data and format_query_results(query_data).strip() not in ["", "SQL_ERROR_OCCURRED", "NO_RESULTS_FOUND"]
    has_doc = document_data and isinstance(document_data, str) and document_data.strip() != ""
    print("Has query: ",has_query)
    print("Has document: ",has_doc)
    formatted_query = format_query_results(query_data) if has_query else "NO_QUERY_DATA"
    formatted_doc = document_data if has_doc else "NO_DOCUMENT_DATA"

    inputs = prompt.format_messages(
        user_question=user_question,
        query_results=formatted_query,
        document_results=formatted_doc,
        formatting_guide=formatting_guide,
        answering_guide=answering_guide,
        response_language=response_language
    )

    result = llm.invoke(inputs)
    return result.content
