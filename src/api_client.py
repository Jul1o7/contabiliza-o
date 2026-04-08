"""
api_client.py - Integração com a API de taxas de câmbio (ExchangeRate-API).

Realiza chamadas REST para buscar cotações de moedas em tempo real.
Documentação da API: https://www.exchangerate-api.com/docs/overview
"""

import os
import requests

# URL base da API (versão gratuita usa endpoint diferente)
_BASE_URL = "https://v6.exchangerate-api.com/v6"
_FREE_URL = "https://open.er-api.com/v6/latest"


def get_exchange_rate(from_currency: str, to_currency: str) -> float | None:
    """
    Busca a taxa de câmbio entre duas moedas usando a ExchangeRate-API.

    Tenta primeiro o endpoint autenticado (se a chave estiver configurada),
    depois cai no endpoint gratuito sem autenticação.

    Args:
        from_currency: Código da moeda de origem (ex.: "USD").
        to_currency: Código da moeda de destino (ex.: "BRL").

    Returns:
        Taxa de conversão (float) ou None se a requisição falhar.

    Exemplos:
        >>> rate = get_exchange_rate("USD", "BRL")
        >>> # Exemplo de saída: 5.12 (USD 1 = BRL 5.12)
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    if from_currency == to_currency:
        return 1.0

    api_key = os.getenv("EXCHANGERATE_API_KEY")

    try:
        if api_key and api_key != "your_exchangerate_api_key_here":
            # Endpoint autenticado com chave da API
            url = f"{_BASE_URL}/{api_key}/latest/{from_currency}"
        else:
            # Endpoint gratuito sem autenticação (limite de uso)
            url = f"{_FREE_URL}/{from_currency}"

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        rates = data.get("conversion_rates") or data.get("rates")
        if rates and to_currency in rates:
            return float(rates[to_currency])

    except requests.exceptions.RequestException as e:
        print(f"[API] Erro ao consultar taxa de câmbio: {e}")
    except (KeyError, ValueError) as e:
        print(f"[API] Erro ao processar resposta da API: {e}")

    return None


def convert_amount(amount: float, from_currency: str, to_currency: str) -> float | None:
    """
    Converte um valor de uma moeda para outra.

    Args:
        amount: Valor a ser convertido.
        from_currency: Código da moeda de origem.
        to_currency: Código da moeda de destino.

    Returns:
        Valor convertido (float) ou None se a taxa não puder ser obtida.

    Exemplos:
        >>> converted = convert_amount(100, "USD", "BRL")
        >>> # Exemplo de saída: 512.0 (100 USD ≈ 512 BRL)
    """
    rate = get_exchange_rate(from_currency, to_currency)
    if rate is not None:
        return round(amount * rate, 2)
    return None


def format_rate_message(from_currency: str, to_currency: str) -> str:
    """
    Retorna uma mensagem formatada com a taxa de câmbio atual.

    Args:
        from_currency: Moeda de origem.
        to_currency: Moeda de destino.

    Returns:
        String formatada para exibição ao usuário.
    """
    rate = get_exchange_rate(from_currency, to_currency)
    if rate is not None:
        return (
            f"💱 Taxa de câmbio atual: 1 {from_currency.upper()} "
            f"= {rate:.4f} {to_currency.upper()}"
        )
    return (
        f"❌ Não foi possível obter a taxa de câmbio para "
        f"{from_currency.upper()} → {to_currency.upper()}. "
        "Verifique sua conexão ou a chave da API."
    )
