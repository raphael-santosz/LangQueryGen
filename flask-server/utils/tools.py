import re

def fix_capitalization_dynamic(query: str) -> str:
    """
    Corrige a capitalização de palavras-chave e nomes comuns de tabelas/colunas.
    """
    keywords = ["SELECT", "FROM", "WHERE", "JOIN", "ON", "GROUP BY", "ORDER BY", "AND", "OR", "INNER", "LEFT", "RIGHT", "AS", "DESC", "ASC"]
    for kw in keywords:
        pattern = re.compile(rf'\b{kw.lower()}\b', re.IGNORECASE)
        query = pattern.sub(kw, query)

    # Exemplo de correção adicional (opcional)
    substitutions = {
        "funcionario": "Funcionario",
        "nome": "Nome",
        "salario": "Salario"
    }
    for original, corrected in substitutions.items():
        pattern = re.compile(rf'\b{original}\b', re.IGNORECASE)
        query = pattern.sub(corrected, query)

    return query

def log_agent_response(question, raw_query, fixed_query, result_data):
    print("\n--- LangQueryGen Debug ---")
    print(f"📩 Pergunta: {question}")
    print(f"🧠 Raw query: {raw_query}")
    print(f"🧼 Fixed query: {fixed_query}")
    print(f"📊 Resultados: {result_data}")
    print("----------------------------\n")
