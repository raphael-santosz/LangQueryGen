from langchain.agents import tool
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain.agents import AgentExecutor
from langchain_ollama import ChatOllama

llm = ChatOllama(model="mistral", temperature=0)

# Ferramenta para validar e ajustar a query
@tool
def validate_and_refine_query(user_question: str, generated_query: str, query_results: list) -> str:
    """
    Recebe a pergunta do usuário, a query gerada pela IA1 e os resultados da consulta ao banco.
    Verifica se a query é adequada e a refina se necessário, retornando uma nova query refinada.
    """
    # Prompt para validar e ajustar a query
    template = """
    A partir da seguinte pergunta do usuário: {user_question}, temos a seguinte query SQL gerada: {generated_query}. 
    Os resultados da consulta ao banco de dados foram: {query_results}.
    O objetivo é verificar se a query gerada responde de forma correta e precisa à pergunta do usuário, considerando os resultados do banco.
    Se necessário, faça ajustes e refinações na query para torná-la mais adequada, sem alterar seu sentido original. 

    Retorne a query refinada ou uma nova query se achar necessário.
    """
    
    prompt = PromptTemplate(input_variables=["user_question", "generated_query", "query_results"], template=template)
    
    # Formatação do prompt
    formatted_prompt = prompt.format(user_question=user_question, generated_query=generated_query, query_results=query_results)
    
    # Invocação do modelo para gerar a nova query
    result = llm.invoke(formatted_prompt)
    
    # A resposta será a query refinada
    return result["text"]

# Prompt de validação de SQL para IA2
promptValid = ChatPromptTemplate.from_messages([
    ("system", "Você é um agente especializado em SQL. Seu objetivo é avaliar e ajustar consultas SQL geradas para garantir que atendam à pergunta do usuário de forma precisa e eficiente. Se necessário, modifique a query gerada para torná-la mais apropriada."),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# Conectando ferramentas e prompt
llm_with_tools = llm.bind_tools([validate_and_refine_query])

# Criação do agente para a IA2
agentValid = (
    {
        "input": lambda x: x["input"],  # Passando a entrada da pergunta
        "agent_scratchpad": lambda x: format_to_openai_tool_messages(x["intermediate_steps"]),
    }
    | promptValid
    | llm_with_tools
    | OpenAIToolsAgentOutputParser()
)

# Executor para IA2
validation_agent_executor = AgentExecutor(agent=agentValid, tools=[validate_and_refine_query], verbose=True)
