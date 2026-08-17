"""
database.py - Módulo de banco de dados SQLite para o tracker de despesas.

Responsável por criar e gerenciar a tabela de despesas, bem como
realizar operações de leitura e escrita no banco.
"""

import sqlite3
import os
from datetime import datetime

# Caminho padrão do banco de dados (na raiz do projeto)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "expenses.db")


def get_connection() -> sqlite3.Connection:
    """Abre e retorna uma conexão com o banco SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permite acesso às colunas por nome
    return conn


def initialize_database() -> None:
    """
    Cria a tabela 'expenses' se ela ainda não existir.
    Schema:
        id          - Identificador único (autoincrement)
        description - Descrição da despesa informada pelo usuário
        amount      - Valor da despesa
        category    - Categoria detectada pela IA (ex.: Alimentação, Transporte)
        currency    - Moeda da despesa (ex.: BRL, USD)
        date        - Data da despesa (YYYY-MM-DD)
        created_at  - Timestamp de criação do registro
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT    NOT NULL,
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL DEFAULT 'Outros',
            currency    TEXT    NOT NULL DEFAULT 'BRL',
            date        TEXT    NOT NULL,
            created_at  TEXT    NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def add_expense(
    description: str,
    amount: float,
    category: str,
    currency: str = "BRL",
    date: str | None = None,
) -> int:
    """
    Insere uma nova despesa no banco de dados.

    Args:
        description: Texto descritivo da despesa.
        amount: Valor gasto.
        category: Categoria classificada pela IA.
        currency: Código da moeda (padrão BRL).
        date: Data da despesa em formato YYYY-MM-DD (padrão: hoje).

    Returns:
        ID do registro inserido.
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO expenses (description, amount, category, currency, date, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (description, amount, category, currency, date, created_at),
    )
    conn.commit()
    expense_id = cursor.lastrowid
    conn.close()
    return expense_id


def get_all_expenses() -> list[dict]:
    """
    Retorna todas as despesas cadastradas, ordenadas da mais recente para a mais antiga.

    Returns:
        Lista de dicionários com os dados de cada despesa.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM expenses ORDER BY date DESC, created_at DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_expenses_by_category(category: str) -> list[dict]:
    """
    Retorna despesas filtradas por categoria.

    Args:
        category: Nome da categoria a filtrar.

    Returns:
        Lista de dicionários com as despesas da categoria.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM expenses WHERE LOWER(category) = LOWER(?) ORDER BY date DESC",
        (category,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_summary_by_category() -> list[dict]:
    """
    Retorna um resumo dos gastos totais agrupados por categoria.

    Returns:
        Lista de dicionários com categoria, total e quantidade de registros.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            category,
            SUM(amount) AS total,
            COUNT(*)    AS count
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_total_spent() -> float:
    """
    Retorna o valor total de todas as despesas cadastradas.

    Returns:
        Soma de todos os valores de despesas.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM expenses")
    result = cursor.fetchone()
    conn.close()
    return float(result["total"])
