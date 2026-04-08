"""
test_api_client.py - Testes para o módulo de integração com a API de câmbio.

Usa mocks para evitar chamadas reais à API durante os testes.
"""

import unittest
from unittest.mock import patch, Mock

from src.api_client import get_exchange_rate, convert_amount, format_rate_message


class TestGetExchangeRate(unittest.TestCase):
    """Testes para a função get_exchange_rate."""

    @patch("src.api_client.requests.get")
    def test_returns_rate_from_free_endpoint(self, mock_get):
        """Deve retornar a taxa de câmbio do endpoint gratuito."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "rates": {"BRL": 5.12, "EUR": 0.92}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        rate = get_exchange_rate("USD", "BRL")
        self.assertAlmostEqual(rate, 5.12)

    @patch("src.api_client.requests.get")
    def test_returns_rate_from_conversion_rates_key(self, mock_get):
        """Deve suportar resposta com chave 'conversion_rates'."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "conversion_rates": {"BRL": 5.25, "EUR": 0.90}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        rate = get_exchange_rate("USD", "BRL")
        self.assertAlmostEqual(rate, 5.25)

    @patch("src.api_client.requests.get")
    def test_returns_none_on_request_error(self, mock_get):
        """Deve retornar None quando a requisição falha."""
        import requests as req
        mock_get.side_effect = req.exceptions.RequestException("timeout")

        rate = get_exchange_rate("USD", "BRL")
        self.assertIsNone(rate)

    @patch("src.api_client.requests.get")
    def test_returns_none_when_currency_not_in_rates(self, mock_get):
        """Deve retornar None quando a moeda alvo não está na resposta."""
        mock_response = Mock()
        mock_response.json.return_value = {"rates": {"EUR": 0.92}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        rate = get_exchange_rate("USD", "XYZ")
        self.assertIsNone(rate)

    def test_same_currency_returns_one(self):
        """Conversão da mesma moeda deve retornar 1.0 sem chamar a API."""
        rate = get_exchange_rate("BRL", "BRL")
        self.assertEqual(rate, 1.0)

    def test_same_currency_case_insensitive(self):
        """Deve normalizar os códigos de moeda para maiúsculas."""
        rate = get_exchange_rate("usd", "USD")
        self.assertEqual(rate, 1.0)


class TestConvertAmount(unittest.TestCase):
    """Testes para a função convert_amount."""

    @patch("src.api_client.get_exchange_rate", return_value=5.0)
    def test_converts_correctly(self, _mock):
        """Deve multiplicar o valor pela taxa de câmbio."""
        result = convert_amount(100.0, "USD", "BRL")
        self.assertAlmostEqual(result, 500.0)

    @patch("src.api_client.get_exchange_rate", return_value=None)
    def test_returns_none_when_rate_unavailable(self, _mock):
        """Deve retornar None quando a taxa não está disponível."""
        result = convert_amount(100.0, "USD", "BRL")
        self.assertIsNone(result)

    @patch("src.api_client.get_exchange_rate", return_value=0.19)
    def test_rounds_to_two_decimals(self, _mock):
        """Resultado deve ser arredondado a 2 casas decimais."""
        result = convert_amount(10.0, "BRL", "USD")
        self.assertEqual(result, 1.90)


class TestFormatRateMessage(unittest.TestCase):
    """Testes para a função format_rate_message."""

    @patch("src.api_client.get_exchange_rate", return_value=5.1234)
    def test_success_message_format(self, _mock):
        """Mensagem de sucesso deve conter as moedas e a taxa."""
        msg = format_rate_message("USD", "BRL")
        self.assertIn("USD", msg)
        self.assertIn("BRL", msg)
        self.assertIn("5.1234", msg)

    @patch("src.api_client.get_exchange_rate", return_value=None)
    def test_failure_message_format(self, _mock):
        """Mensagem de erro deve indicar falha na consulta."""
        msg = format_rate_message("USD", "XYZ")
        self.assertIn("❌", msg)
        self.assertIn("USD", msg)
        self.assertIn("XYZ", msg)


if __name__ == "__main__":
    unittest.main()
