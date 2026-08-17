"""
chatbot.py - Interface conversacional do tracker de despesas.

Gerencia o loop de interação com o usuário, interpreta comandos e
aciona os módulos de banco de dados, IA (chains) e API de câmbio.

Comandos disponíveis:
    ver           - Lista todas as despesas cadastradas
    resumo        - Exibe total gasto por categoria
    câmbio        - Consulta taxa de câmbio (ex.: câmbio USD BRL)
    ajuda         - Exibe lista de comandos
    sair          - Encerra o chatbot
    <mensagem>    - Registra uma nova despesa (ex.: "Gastei R$50 em comida")
"""

import os
import sys

from dotenv import load_dotenv

# Carrega variáveis do arquivo .env (se existir)
load_dotenv()

# Importações dos módulos do projeto
from src.database import (
    initialize_database,
    add_expense,
    get_all_expenses,
    get_summary_by_category,
    get_total_spent,
)
from src.expense_chain import process_expense_message, SUPPORTED_CATEGORIES
from src.api_client import format_rate_message

# ---------------------------------------------------------------------------
# Constantes de interface
# ---------------------------------------------------------------------------
_BANNER = """
╔══════════════════════════════════════════════════════╗
║         💰  Contabiliza-o — Tracker de Despesas      ║
║     Seu assistente pessoal de finanças com IA 🤖     ║
╚══════════════════════════════════════════════════════╝
Digite uma despesa, ex.: "Gastei R$50 em comida"
Digite "ajuda" para ver todos os comandos disponíveis.
"""

_HELP_TEXT = """
📋 Comandos disponíveis:
  ver           → Lista todas as despesas registradas
  resumo        → Exibe o total gasto por categoria
  câmbio <DE> <PARA>
                → Consulta a taxa de câmbio
                  (ex.: câmbio USD BRL)
  ajuda         → Mostra esta mensagem
  sair / exit   → Encerra o programa

📝 Para registrar uma despesa, basta digitar naturalmente:
  "Gastei R$30 no almoço"
  "Paguei 50 de uber"
  "Netflix me custou 45 reais"
  "I spent $20 on groceries"
"""

# ---------------------------------------------------------------------------
# Funções auxiliares de formatação
# ---------------------------------------------------------------------------


def _format_expense_row(expense: dict) -> str:
    """Formata uma linha de despesa para exibição no terminal."""
    return (
        f"  [{expense['id']:>3}] {expense['date']}  "
        f"{expense['currency']} {expense['amount']:>10.2f}  "
        f"{expense['category']:<15}  {expense['description']}"
    )


def _print_expenses(expenses: list[dict]) -> None:
    """Exibe a lista de despesas no terminal."""
    if not expenses:
        print("📭 Nenhuma despesa registrada ainda.")
        return

    print(f"\n{'─'*70}")
    print(f"  {'ID':>3}  {'Data':<12}  {'Moeda':<6}  {'Valor':>10}  {'Categoria':<15}  Descrição")
    print(f"{'─'*70}")
    for exp in expenses:
        print(_format_expense_row(exp))
    print(f"{'─'*70}")
    total = get_total_spent()
    print(f"  Total registrado: {total:.2f}\n")


def _print_summary(summary: list[dict]) -> None:
    """Exibe o resumo de gastos por categoria."""
    if not summary:
        print("📭 Nenhuma despesa registrada ainda.")
        return

    total = sum(row["total"] for row in summary)
    print(f"\n{'─'*45}")
    print(f"  {'Categoria':<20}  {'Total':>10}  {'Qtd':>5}")
    print(f"{'─'*45}")
    for row in summary:
        pct = (row["total"] / total * 100) if total > 0 else 0
        print(
            f"  {row['category']:<20}  {row['total']:>10.2f}  "
            f"{row['count']:>4}x  ({pct:.1f}%)"
        )
    print(f"{'─'*45}")
    print(f"  {'TOTAL':<20}  {total:>10.2f}\n")


# ---------------------------------------------------------------------------
# Processamento de comandos
# ---------------------------------------------------------------------------


def _handle_command(user_input: str) -> bool:
    """
    Interpreta a entrada do usuário e executa o comando ou registra a despesa.

    Args:
        user_input: Texto digitado pelo usuário.

    Returns:
        False se o usuário quiser sair, True caso contrário.
    """
    text = user_input.strip()

    if not text:
        return True

    lower = text.lower()

    # Comando: sair
    if lower in ("sair", "exit", "quit", "q"):
        print("\n👋 Até logo! Bons controles financeiros! 💸\n")
        return False

    # Comando: ajuda
    if lower in ("ajuda", "help", "?"):
        print(_HELP_TEXT)
        return True

    # Comando: ver despesas
    if lower.startswith("ver"):
        expenses = get_all_expenses()
        _print_expenses(expenses)
        return True

    # Comando: resumo por categoria
    if lower.startswith("resumo"):
        summary = get_summary_by_category()
        _print_summary(summary)
        return True

    # Comando: câmbio <DE> <PARA>
    if lower.startswith("câmbio") or lower.startswith("cambio"):
        parts = text.split()
        if len(parts) == 3:
            _, from_cur, to_cur = parts
            print(format_rate_message(from_cur, to_cur))
        else:
            print("💡 Uso correto: câmbio <MOEDA_ORIGEM> <MOEDA_DESTINO>")
            print("   Exemplo: câmbio USD BRL")
        return True

    # Registrar nova despesa (linguagem natural)
    print("🤔 Analisando sua despesa...")
    result = process_expense_message(text)

    if result["amount"] <= 0:
        print(
            "❓ Não consegui identificar o valor da despesa. "
            "Tente: \"Gastei R$50 em comida\""
        )
        return True

    expense_id = add_expense(
        description=result["description"],
        amount=result["amount"],
        category=result["category"],
        currency=result["currency"],
    )

    print(
        f"\n✅ Despesa registrada com sucesso!\n"
        f"   ID          : #{expense_id}\n"
        f"   Descrição   : {result['description']}\n"
        f"   Valor       : {result['currency']} {result['amount']:.2f}\n"
        f"   Categoria   : {result['category']}\n"
    )

    return True


# ---------------------------------------------------------------------------
# Loop principal do chatbot
# ---------------------------------------------------------------------------


def run_chatbot() -> None:
    """
    Inicia o loop principal do chatbot de despesas.

    Verifica se a chave da OpenAI está configurada antes de iniciar.
    Inicializa o banco de dados e entra no loop de interação.
    """
    # Verifica configuração da API OpenAI
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key == "your_openai_api_key_here":
        print(
            "\n⚠️  AVISO: OPENAI_API_KEY não configurada.\n"
            "   A categorização automática com IA não funcionará.\n"
            "   Configure a variável no arquivo .env (veja .env.example).\n"
            "   O tracker ainda pode ser usado para registrar despesas manualmente.\n"
        )

    # Inicializa o banco de dados
    initialize_database()

    print(_BANNER)

    # Loop de interação
    try:
        while True:
            try:
                user_input = input("Você: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\n👋 Encerrando... Até logo!\n")
                break

            should_continue = _handle_command(user_input)
            if not should_continue:
                break
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)
