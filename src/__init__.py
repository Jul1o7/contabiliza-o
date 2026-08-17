"""
__init__.py - Pacote src do Contabiliza-o.

Exporta os principais componentes para facilitar o uso externo.
"""

from src.database import (
    initialize_database,
    add_expense,
    get_all_expenses,
    get_expenses_by_category,
    get_summary_by_category,
    get_total_spent,
)
from src.api_client import get_exchange_rate, convert_amount, format_rate_message
from src.expense_chain import (
    extract_expense_info,
    categorize_expense,
    process_expense_message,
    SUPPORTED_CATEGORIES,
)

__all__ = [
    # database
    "initialize_database",
    "add_expense",
    "get_all_expenses",
    "get_expenses_by_category",
    "get_summary_by_category",
    "get_total_spent",
    # api_client
    "get_exchange_rate",
    "convert_amount",
    "format_rate_message",
    # expense_chain
    "extract_expense_info",
    "categorize_expense",
    "process_expense_message",
    "SUPPORTED_CATEGORIES",
]
