"""
test_expense_chain.py - Testes para as chains LangChain de categorização.

Usa mocks para substituir chamadas à API OpenAI durante os testes,
permitindo execução offline e sem custos.
"""

import json
import unittest
from unittest.mock import patch, MagicMock

from src.expense_chain import (
    extract_expense_info,
    categorize_expense,
    process_expense_message,
    SUPPORTED_CATEGORIES,
)


def _mock_llm_chain(return_value: str):
    """Helper que mocka o pipeline LangChain (prompt | llm | parser) para retornar um valor fixo."""
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = return_value
    return mock_chain


class TestSupportedCategories(unittest.TestCase):
    """Testes para a lista de categorias suportadas."""

    def test_categories_not_empty(self):
        """Deve haver pelo menos uma categoria definida."""
        self.assertGreater(len(SUPPORTED_CATEGORIES), 0)

    def test_categories_are_strings(self):
        """Todas as categorias devem ser strings."""
        for cat in SUPPORTED_CATEGORIES:
            self.assertIsInstance(cat, str)

    def test_alimentacao_in_categories(self):
        """'Alimentação' deve ser uma das categorias suportadas."""
        self.assertIn("Alimentação", SUPPORTED_CATEGORIES)

    def test_outros_in_categories(self):
        """'Outros' deve ser a categoria padrão/fallback."""
        self.assertIn("Outros", SUPPORTED_CATEGORIES)


class TestExtractExpenseInfo(unittest.TestCase):
    """Testes para a função extract_expense_info."""

    def test_extracts_amount_and_description(self):
        """Deve extrair corretamente valor, descrição e moeda."""
        from langchain_core.runnables import RunnableLambda

        expected_json = json.dumps(
            {"amount": 50.0, "description": "comida", "currency": "BRL"}
        )
        # Substitui o prompt, o LLM e o parser por RunnableLambda passthrough
        with (
            patch(
                "src.expense_chain._EXTRACT_PROMPT",
                RunnableLambda(lambda _: expected_json),
            ),
            patch(
                "src.expense_chain._build_llm",
                return_value=RunnableLambda(lambda x: x),
            ),
            patch(
                "src.expense_chain.StrOutputParser",
                return_value=RunnableLambda(lambda x: x),
            ),
        ):
            result = extract_expense_info("Gastei R$50 em comida")

        self.assertEqual(result["amount"], 50.0)
        self.assertEqual(result["description"], "comida")
        self.assertEqual(result["currency"], "BRL")

    @patch("src.expense_chain._build_llm")
    def test_returns_defaults_on_llm_error(self, mock_build_llm):
        """Deve retornar valores padrão quando o LLM lança exceção."""
        mock_build_llm.side_effect = Exception("API Error")

        result = extract_expense_info("qualquer mensagem")

        self.assertEqual(result["amount"], 0.0)
        self.assertEqual(result["currency"], "BRL")
        self.assertIsInstance(result["description"], str)


class TestCategorizeExpense(unittest.TestCase):
    """Testes para a função categorize_expense."""

    def test_returns_valid_category(self):
        """Deve retornar uma categoria válida da lista."""
        from langchain_core.runnables import RunnableLambda

        with (
            patch(
                "src.expense_chain._CATEGORY_PROMPT",
                RunnableLambda(lambda _: "Alimentação"),
            ),
            patch(
                "src.expense_chain._build_llm",
                return_value=RunnableLambda(lambda x: x),
            ),
            patch(
                "src.expense_chain.StrOutputParser",
                return_value=RunnableLambda(lambda x: x),
            ),
        ):
            category = categorize_expense("comida")

        self.assertIn(category, SUPPORTED_CATEGORIES)

    @patch("src.expense_chain._build_llm")
    def test_falls_back_to_outros_on_error(self, mock_build_llm):
        """Deve retornar 'Outros' quando o LLM não responde."""
        mock_build_llm.side_effect = Exception("API unavailable")

        category = categorize_expense("qualquer coisa")
        self.assertEqual(category, "Outros")

    def test_falls_back_to_outros_for_unknown_category(self):
        """Deve retornar 'Outros' quando a resposta não é uma categoria válida."""
        from langchain_core.runnables import RunnableLambda

        with (
            patch(
                "src.expense_chain._CATEGORY_PROMPT",
                RunnableLambda(lambda _: "CategoriaInexistente"),
            ),
            patch(
                "src.expense_chain._build_llm",
                return_value=RunnableLambda(lambda x: x),
            ),
            patch(
                "src.expense_chain.StrOutputParser",
                return_value=RunnableLambda(lambda x: x),
            ),
        ):
            category = categorize_expense("algo estranho")

        self.assertEqual(category, "Outros")


class TestProcessExpenseMessage(unittest.TestCase):
    """Testes para o pipeline completo process_expense_message."""

    @patch("src.expense_chain.categorize_expense", return_value="Alimentação")
    @patch(
        "src.expense_chain.extract_expense_info",
        return_value={"amount": 30.0, "description": "almoço", "currency": "BRL"},
    )
    def test_full_pipeline(self, _mock_extract, _mock_categorize):
        """Pipeline deve combinar extração e categorização corretamente."""
        result = process_expense_message("Gastei R$30 no almoço")

        self.assertEqual(result["amount"], 30.0)
        self.assertEqual(result["description"], "almoço")
        self.assertEqual(result["currency"], "BRL")
        self.assertEqual(result["category"], "Alimentação")

    @patch("src.expense_chain.categorize_expense", return_value="Outros")
    @patch(
        "src.expense_chain.extract_expense_info",
        return_value={"amount": 0.0, "description": "mensagem vaga", "currency": "BRL"},
    )
    def test_pipeline_with_zero_amount(self, _mock_extract, _mock_categorize):
        """Pipeline deve funcionar mesmo com valor zero."""
        result = process_expense_message("alguma coisa")
        self.assertEqual(result["amount"], 0.0)
        self.assertEqual(result["category"], "Outros")


if __name__ == "__main__":
    unittest.main()
