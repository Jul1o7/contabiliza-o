"""
test_database.py - Testes unitários para o módulo de banco de dados.

Usa um banco SQLite temporário para isolar os testes.
"""

import os
import tempfile
import unittest

# Cria um arquivo temporário seguro para o banco durante os testes
_TEMP_FD, _TEMP_DB = tempfile.mkstemp(suffix=".db")
os.close(_TEMP_FD)  # Fecha o file descriptor; o SQLite abrirá o arquivo por conta própria

import src.database as db

# Sobrescreve o caminho do banco para o arquivo temporário
db.DB_PATH = _TEMP_DB


class TestDatabase(unittest.TestCase):
    """Testes para as funções do módulo database.py."""

    def setUp(self):
        """Recria o banco vazio antes de cada teste."""
        if os.path.exists(_TEMP_DB):
            os.remove(_TEMP_DB)
        db.initialize_database()

    def tearDown(self):
        """Remove o banco temporário após cada teste."""
        if os.path.exists(_TEMP_DB):
            os.remove(_TEMP_DB)

    # ------------------------------------------------------------------
    # initialize_database
    # ------------------------------------------------------------------

    def test_initialize_creates_table(self):
        """Verifica que a tabela 'expenses' é criada."""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='expenses'"
        )
        result = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(result)

    # ------------------------------------------------------------------
    # add_expense
    # ------------------------------------------------------------------

    def test_add_expense_returns_id(self):
        """add_expense deve retornar um ID inteiro válido."""
        expense_id = db.add_expense("almoço", 30.0, "Alimentação")
        self.assertIsInstance(expense_id, int)
        self.assertGreater(expense_id, 0)

    def test_add_expense_persists_data(self):
        """Despesa adicionada deve estar presente na listagem."""
        db.add_expense("uber", 15.50, "Transporte", "BRL", "2024-01-15")
        expenses = db.get_all_expenses()
        self.assertEqual(len(expenses), 1)
        exp = expenses[0]
        self.assertEqual(exp["description"], "uber")
        self.assertAlmostEqual(exp["amount"], 15.50)
        self.assertEqual(exp["category"], "Transporte")
        self.assertEqual(exp["currency"], "BRL")
        self.assertEqual(exp["date"], "2024-01-15")

    def test_add_expense_defaults_currency_to_brl(self):
        """Moeda padrão deve ser BRL quando não informada."""
        db.add_expense("café", 5.0, "Alimentação")
        expenses = db.get_all_expenses()
        self.assertEqual(expenses[0]["currency"], "BRL")

    def test_add_multiple_expenses(self):
        """Deve suportar múltiplas despesas."""
        db.add_expense("comida", 50.0, "Alimentação")
        db.add_expense("ônibus", 4.5, "Transporte")
        db.add_expense("livro", 80.0, "Educação")
        expenses = db.get_all_expenses()
        self.assertEqual(len(expenses), 3)

    # ------------------------------------------------------------------
    # get_all_expenses
    # ------------------------------------------------------------------

    def test_get_all_expenses_empty(self):
        """Deve retornar lista vazia quando não há despesas."""
        expenses = db.get_all_expenses()
        self.assertEqual(expenses, [])

    def test_get_all_expenses_returns_dicts(self):
        """Despesas devem ser retornadas como dicionários."""
        db.add_expense("jantar", 60.0, "Alimentação")
        expenses = db.get_all_expenses()
        self.assertIsInstance(expenses[0], dict)
        self.assertIn("id", expenses[0])
        self.assertIn("amount", expenses[0])
        self.assertIn("category", expenses[0])

    # ------------------------------------------------------------------
    # get_expenses_by_category
    # ------------------------------------------------------------------

    def test_get_expenses_by_category_filters_correctly(self):
        """Deve retornar apenas as despesas da categoria informada."""
        db.add_expense("pizza", 40.0, "Alimentação")
        db.add_expense("uber", 20.0, "Transporte")
        db.add_expense("sushi", 80.0, "Alimentação")

        food = db.get_expenses_by_category("Alimentação")
        self.assertEqual(len(food), 2)
        for exp in food:
            self.assertEqual(exp["category"], "Alimentação")

    def test_get_expenses_by_category_case_insensitive(self):
        """Filtro por categoria deve ser insensível a maiúsculas."""
        db.add_expense("pizza", 40.0, "Alimentação")
        result = db.get_expenses_by_category("alimentação")
        self.assertEqual(len(result), 1)

    def test_get_expenses_by_category_nonexistent(self):
        """Deve retornar lista vazia para categoria inexistente."""
        db.add_expense("pizza", 40.0, "Alimentação")
        result = db.get_expenses_by_category("Saúde")
        self.assertEqual(result, [])

    # ------------------------------------------------------------------
    # get_summary_by_category
    # ------------------------------------------------------------------

    def test_get_summary_by_category(self):
        """Resumo deve agregar corretamente os valores por categoria."""
        db.add_expense("almoço", 30.0, "Alimentação")
        db.add_expense("jantar", 50.0, "Alimentação")
        db.add_expense("uber", 20.0, "Transporte")

        summary = db.get_summary_by_category()
        self.assertEqual(len(summary), 2)

        food = next(s for s in summary if s["category"] == "Alimentação")
        self.assertAlmostEqual(food["total"], 80.0)
        self.assertEqual(food["count"], 2)

    def test_get_summary_empty_db(self):
        """Resumo em banco vazio deve retornar lista vazia."""
        summary = db.get_summary_by_category()
        self.assertEqual(summary, [])

    # ------------------------------------------------------------------
    # get_total_spent
    # ------------------------------------------------------------------

    def test_get_total_spent(self):
        """Total gasto deve somar todas as despesas corretamente."""
        db.add_expense("a", 10.0, "Outros")
        db.add_expense("b", 20.5, "Outros")
        db.add_expense("c", 5.75, "Outros")
        total = db.get_total_spent()
        self.assertAlmostEqual(total, 36.25)

    def test_get_total_spent_empty(self):
        """Total em banco vazio deve ser 0.0."""
        total = db.get_total_spent()
        self.assertAlmostEqual(total, 0.0)


if __name__ == "__main__":
    unittest.main()
