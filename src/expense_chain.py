"""
expense_chain.py - Chains LangChain para categorização de despesas com IA.

Usa OpenAI via LangChain para:
1. Extrair valor e descrição de mensagens em linguagem natural.
2. Classificar automaticamente a categoria da despesa.

Fluxo (chain):
    Mensagem do usuário
        → Prompt de extração → LLM → JSON (valor + descrição)
        → Prompt de categorização → LLM → Categoria
"""

import json
import os
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

# ---------------------------------------------------------------------------
# Categorias suportadas
# ---------------------------------------------------------------------------
SUPPORTED_CATEGORIES = [
    "Alimentação",
    "Transporte",
    "Moradia",
    "Saúde",
    "Lazer",
    "Educação",
    "Roupas",
    "Tecnologia",
    "Serviços",
    "Outros",
]

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

# Prompt para extrair valor e descrição de uma frase em linguagem natural
_EXTRACT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "Você é um assistente especializado em finanças pessoais. "
                "Sua tarefa é extrair informações de despesa de uma mensagem do usuário. "
                "Retorne APENAS um JSON válido com os campos:\n"
                '  "amount": número decimal (ex: 50.0)\n'
                '  "description": string curta descrevendo o item/serviço\n'
                '  "currency": código ISO da moeda (ex: "BRL", "USD", "EUR")\n\n'
                "Se não conseguir identificar o valor, use 0.0. "
                "Se não conseguir identificar a moeda, use BRL. "
                "Não inclua texto fora do JSON."
            ),
        ),
        ("human", "{user_message}"),
    ]
)

# Prompt para classificar a categoria da despesa
_CATEGORY_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "Você é um assistente de controle financeiro. "
                "Classifique a despesa descrita em UMA das categorias abaixo:\n"
                f"{chr(10).join(f'- {c}' for c in SUPPORTED_CATEGORIES)}\n\n"
                "Retorne APENAS o nome da categoria, sem pontuação ou texto adicional."
            ),
        ),
        ("human", "Despesa: {description}"),
    ]
)


# ---------------------------------------------------------------------------
# Funções públicas
# ---------------------------------------------------------------------------


def _build_llm() -> ChatOpenAI:
    """Instancia o modelo de linguagem da OpenAI."""
    return ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )


def extract_expense_info(user_message: str) -> dict:
    """
    Extrai valor, descrição e moeda de uma mensagem em linguagem natural.

    Utiliza um LLM (via LangChain) para interpretar frases como:
        "Gastei R$50 em comida" → {"amount": 50.0, "description": "comida", "currency": "BRL"}

    Args:
        user_message: Mensagem do usuário descrevendo a despesa.

    Returns:
        Dicionário com chaves "amount" (float), "description" (str) e "currency" (str).
        Em caso de erro, retorna valores padrão.
    """
    try:
        llm = _build_llm()
        chain = _EXTRACT_PROMPT | llm | StrOutputParser()
        result = chain.invoke({"user_message": user_message})

        # Tenta parsear o JSON retornado pelo LLM
        # Remove possível markdown code block (```json ... ```)
        cleaned = re.sub(r"```[a-z]*\n?", "", result).strip()
        data = json.loads(cleaned)

        return {
            "amount": float(data.get("amount", 0.0)),
            "description": str(data.get("description", user_message)),
            "currency": str(data.get("currency", "BRL")).upper(),
        }
    except Exception as e:
        print(f"[Chain] Erro ao extrair informações: {e}")
        return {"amount": 0.0, "description": user_message, "currency": "BRL"}


def categorize_expense(description: str) -> str:
    """
    Classifica uma despesa em uma das categorias suportadas usando IA.

    Args:
        description: Descrição curta da despesa (ex.: "comida", "uber", "netflix").

    Returns:
        Nome da categoria (string), ex.: "Alimentação", "Transporte".
        Retorna "Outros" em caso de falha.
    """
    try:
        llm = _build_llm()
        chain = _CATEGORY_PROMPT | llm | StrOutputParser()
        category = chain.invoke({"description": description}).strip()

        # Valida se a categoria retornada é uma das suportadas
        if category in SUPPORTED_CATEGORIES:
            return category

        # Tenta correspondência parcial (insensível a maiúsculas)
        for supported in SUPPORTED_CATEGORIES:
            if supported.lower() in category.lower():
                return supported

        return "Outros"
    except Exception as e:
        print(f"[Chain] Erro ao categorizar despesa: {e}")
        return "Outros"


def process_expense_message(user_message: str) -> dict:
    """
    Pipeline completo: extrai e categoriza uma despesa a partir de uma mensagem.

    Combina extract_expense_info + categorize_expense em um fluxo único (chain).

    Args:
        user_message: Mensagem do usuário, ex.: "Gastei 30 reais no almoço".

    Returns:
        Dicionário com:
            - amount (float): Valor da despesa.
            - description (str): Descrição identificada.
            - currency (str): Código da moeda.
            - category (str): Categoria classificada pela IA.
    """
    # Passo 1: Extrair informações da mensagem
    info = extract_expense_info(user_message)

    # Passo 2: Categorizar com base na descrição
    category = categorize_expense(info["description"])

    return {**info, "category": category}
