import unittest
from unittest.mock import patch, Mock
import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nodebalance import plugin, node_balance, RATES_CACHE, CONVERSION_RATES

class TestNodeBalanceFallback(unittest.TestCase):
    def setUp(self):
        """Reset plugin and cache."""
        self.plugin = plugin
        self.plugin.log = Mock()
        RATES_CACHE["rates"] = CONVERSION_RATES.copy()
        RATES_CACHE["timestamp"] = 0

    def _mock_rates(self):
        """Common mock rates for gbp, eur."""
        return {"gbp": 78000, "eur": 91604}

    @patch('nodebalance.time.time')
    @patch('nodebalance.requests.get')
    def test_coingecko_success(self, mock_get, mock_time):
        """Test CoinGecko succeeds, no further APIs called."""
        mock_time.return_value = 10000000
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = {"bitcoin": self._mock_rates()}
        mock_get.return_value = mock_response

        result = node_balance(self.plugin, mode="rate", currencies="gbp,eur")
        expected_rates = {"gbp": "78,000.00 GBP", "eur": "91,604.00 EUR"}
        self.assertEqual(result["rates"], expected_rates)
        self.assertTrue(result["cached"])

        log_calls = [call[0][0] for call in self.plugin.log.call_args_list]
        self.assertIn("Fetching rates from CoinGecko for: gbp,eur", log_calls)
        self.assertNotIn("Fetching rates from CoinPaprika", log_calls)
        self.assertTrue(RATES_CACHE["rates"]["gbp"] > 0)

    @patch('nodebalance.time.time')
    @patch('nodebalance.requests.get')
    def test_coingecko_fails_coinpaprika_success(self, mock_get, mock_time):
        """Test CoinGecko fails, CoinPaprika succeeds."""
        mock_time.return_value = 10000000
        def side_effect(url, *args, **kwargs):
            if "coingecko" in url:
                raise requests.exceptions.RequestException("CoinGecko down")
            mock_response = Mock(status_code=200)
            mock_response.json.return_value = {"quotes": {k.upper(): {"price": v} for k, v in self._mock_rates().items()}}
            return mock_response

        mock_get.side_effect = side_effect

        result = node_balance(self.plugin, mode="rate", currencies="gbp,eur")
        expected_rates = {"gbp": "78,000.00 GBP", "eur": "91,604.00 EUR"}
        self.assertEqual(result["rates"], expected_rates)
        self.assertTrue(result["cached"])

        log_calls = [call[0][0] for call in self.plugin.log.call_args_list]
        self.assertIn("CoinGecko API failed: CoinGecko down", log_calls)
        self.assertIn("Fetching rates from CoinPaprika for: gbp,eur", log_calls)
        self.assertNotIn("Fetching rates from CoinCap", log_calls)
        self.assertTrue(RATES_CACHE["rates"]["gbp"] > 0)

    @patch('nodebalance.time.time')
    @patch('nodebalance.requests.get')
    def test_coingecko_coinpaprika_fails_coincap_success(self, mock_get, mock_time):
        """Test CoinGecko and CoinPaprika fail, CoinCap succeeds."""
        mock_time.return_value = 10000000
        def side_effect(url, *args, **kwargs):
            if "coingecko" in url:
                raise requests.exceptions.RequestException("CoinGecko down")
            if "coinpaprika" in url:
                raise requests.exceptions.RequestException("CoinPaprika down")
            if "rates/bitcoin" in url:
                return Mock(status_code=200, json=lambda: {"data": {"id": "bitcoin", "rateUsd": 100000}})
            if "rates" in url:
                return Mock(status_code=200, json=lambda: {"data": [
                    {"id": "gbp", "rateUsd": 1.282},
                    {"id": "eur", "rateUsd": 1.092}
                ]})
            raise ValueError("Unexpected URL")

        mock_get.side_effect = side_effect

        result = node_balance(self.plugin, mode="rate", currencies="gbp,eur")
        expected_rates = {"gbp": "78,003.12 GBP", "eur": "91,575.09 EUR"}
        self.assertEqual(result["rates"], expected_rates)
        self.assertTrue(result["cached"])

        log_calls = [call[0][0] for call in self.plugin.log.call_args_list]
        self.assertIn("CoinGecko API failed: CoinGecko down", log_calls)
        self.assertIn("CoinPaprika API failed: CoinPaprika down", log_calls)
        self.assertIn("Fetching rates from CoinCap for: gbp,eur", log_calls)
        self.assertTrue(RATES_CACHE["rates"]["gbp"] > 0)

    @patch('nodebalance.time.time')
    @patch('nodebalance.requests.get')
    def test_all_apis_fail(self, mock_get, mock_time):
        """Test all APIs fail, falls back to CONVERSION_RATES."""
        mock_time.return_value = 10000000
        mock_get.side_effect = requests.exceptions.RequestException("API down")

        result = node_balance(self.plugin, mode="rate", currencies="gbp,eur,usd,mxn")
        expected_rates = {
            "gbp": "Rate unavailable",
            "eur": "Rate unavailable",
            "usd": "100,000,000,000,000,000.00 USD",
            "mxn": "2,000,000,000,000,000.00 MXN"
        }
        self.assertEqual(result["rates"], expected_rates)
        self.assertTrue(result["cached"])

        log_calls = [call[0][0] for call in self.plugin.log.call_args_list]
        self.assertIn("CoinGecko API failed: API down", log_calls)
        self.assertIn("CoinPaprika API failed: API down", log_calls)
        self.assertIn("CoinCap API failed: API down", log_calls)
        self.assertIn("No fallback available for gbp", log_calls)

if __name__ == '__main__':
    unittest.main()
    