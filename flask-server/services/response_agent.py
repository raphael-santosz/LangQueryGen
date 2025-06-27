from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, PromptTemplate
from utils.tools import carregar_guides_md, carregar_prompt, format_query_results, remove_markdown
from langdetect import detect

# Inicializar modelo
llm = ChatOllama(model="gemma:7b-instruct", temperature=0)

# Carregar guias de estilo e resposta
formatting_guide = carregar_guides_md("utils/formatting_guide.md")
answering_guide = carregar_guides_md("utils/answering_guide.md")

# Carregar template principal
template = carregar_prompt("prompts/user_chatbot.txt")

# Criar prompt composto
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

# Função principal da IA3
def generate_answer(user_question, query_data, document_data, blocked=False):
    # Detectar idioma da pergunta
    print("🔒 Status de segurança (blocked):", blocked)
    lang = detect(user_question)
    response_language = {'en': 'English', 'es': 'Spanish', 'pt': 'Portuguese'}.get(lang, 'English')
    if blocked:
        messages = {
            'pt': "⛔ O acesso a essas informações é restrito. Por questões de privacidade, não posso fornecer os dados solicitados.",
            'es': "⛔ El acceso a esta información está restringido. Por motivos de privacidad, no puedo proporcionarla.",
            'en': "⛔ Access to this information is restricted. Due to privacy reasons, I cannot provide the requested data."
        }
        return messages.get(lang, messages['en'])

    # Verificações de conteúdo
    formatted_query = format_query_results(query_data)
    has_query = formatted_query.strip() not in ["", "SQL_ERROR_OCCURRED", "NO_RESULTS_FOUND"]

    has_doc = (
        isinstance(document_data, str)
        and document_data.strip().upper() not in ["", "NO_DOCUMENT_DATA", "NO_RELEVANT_DATA_FOUND"]
    )

    print("Has query:", has_query)
    print("Has document:", has_doc)

    query_input = formatted_query if has_query else "NO_QUERY_DATA"
    doc_input = document_data if has_doc else "NO_DOCUMENT_DATA"

    # Montar entrada para o modelo
    inputs = prompt.format_messages(
        user_question=user_question,
        query_results=query_input,
        document_results=doc_input,
        formatting_guide=formatting_guide,
        answering_guide=answering_guide,
        response_language=response_language
    )

    # Debug opcional
    #print("--- DEBUG IA3 INPUTS ---")
    #print("user_question:", user_question)
    #print("query_results:", query_input)
    #print("document_results:", doc_input)
    #print("response_language:", response_language)

    # Executar modelo
    result = llm.invoke(inputs)
    
    return remove_markdown(result.content)
