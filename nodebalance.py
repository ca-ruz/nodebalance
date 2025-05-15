#!/usr/bin/env python3
from pyln.client import Plugin
import json
import requests
import time
from datetime import datetime
from collections import OrderedDict

plugin = Plugin()

# Valid fiat currencies supported by CoinGecko (fetched manually from /simple/supported_vs_currencies, crypto excluded)
VALID_CURRENCIES = [
    "aed", "ars", "aud", "bdt", "bhd", "bmd", "brl", "cad", "chf", "clp",
    "cny", "czk", "dkk", "eur", "gbp", "hkd", "huf", "idr", "ils", "inr",
    "jpy", "krw", "kwd", "lkr", "mmk", "mxn", "myr", "ngn", "nok", "nzd",
    "php", "pkr", "pln", "rub", "sar", "sek", "sgd", "thb", "try", "twd",
    "uah", "usd", "vef", "vnd", "xag", "xau", "xdr", "zar"
]

# Default currencies and fallback rates (msat as base)
DEFAULT_CURRENCIES = ["usd", "mxn"]
CONVERSION_RATES = {
    "msats": 1,  # Base unit
    "sats": 1000,  # 1 sat = 1000 msat
    "btc": 100000000000,  # 1 BTC = 100,000,000,000 msat
    "mxn": 0.00005,  # Fallback: 1 msat = 0.00005 MXN (1 BTC ≈ 2,000,000 MXN)
    "usd": 0.000001   # Fallback: 1 msat = 0.000001 USD (1 BTC ≈ 100,000 USD)
}

# Cache for currency rates
RATES_CACHE = {"rates": CONVERSION_RATES, "timestamp": 0}
CACHE_TIMEOUT = 3600  # Cache rates for 1 hour

def fetch_coingecko_rates(currencies):
    """Fetch rates from CoinGecko API."""
    try:
        currency_param = ",".join(currencies)
        url = f"https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies={currency_param}"
        plugin.log(f"Fetching rates from CoinGecko for: {currency_param}")
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        btc_rates = data.get("bitcoin", {})
        plugin.log(f"CoinGecko response: {json.dumps(btc_rates, indent=2)}")
        return btc_rates
    except Exception as e:
        plugin.log(f"CoinGecko API failed: {str(e)}")
        return None

def fetch_coinpaprika_rates(currencies):
    """Fetch rates from CoinPaprika API."""
    try:
        url = "https://api.coinpaprika.com/v1/tickers/btc-bitcoin"
        plugin.log(f"Fetching rates from CoinPaprika for: {','.join(currencies)}")
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        quotes = data.get("quotes", {})
        btc_rates = {c.lower(): quotes[c.upper()]["price"] for c in currencies if c.upper() in quotes}
        plugin.log(f"CoinPaprika response: {json.dumps(btc_rates, indent=2)}")
        return btc_rates
    except Exception as e:
        plugin.log(f"CoinPaprika API failed: {str(e)}")
        return None

def fetch_coincap_rates(currencies):
    """Fetch rates from CoinCap API."""
    try:
        btc_url = "https://api.coincap.io/v2/rates/bitcoin"
        rates_url = "https://api.coincap.io/v2/rates"
        plugin.log(f"Fetching rates from CoinCap for: {','.join(currencies)}")
        btc_response = requests.get(btc_url, timeout=5)
        btc_response.raise_for_status()
        rates_response = requests.get(rates_url, timeout=5)
        rates_response.raise_for_status()
        btc_data = btc_response.json()["data"]
        rates_data = {rate["id"].lower(): float(rate["rateUsd"]) for rate in rates_response.json()["data"]}
        btc_usd = float(btc_data["rateUsd"])
        btc_rates = {c: btc_usd / rates_data[c] for c in currencies if c in rates_data}
        plugin.log(f"CoinCap response: {json.dumps(btc_rates, indent=2)}")
        return btc_rates
    except Exception as e:
        plugin.log(f"CoinCap API failed: {str(e)}")
        return None

def get_currency_rates(currencies):
    """
    Fetch real-time BTC to specified currency rates from multiple APIs.
    Caches rates to minimize API calls, refreshes if currencies are missing or rates are invalid.
    """
    current_time = time.time()
    cached_rates = RATES_CACHE["rates"]
    plugin.log(f"Checking cache: timestamp={RATES_CACHE['timestamp']}, rates={cached_rates}")

    # Check if cache is fresh and all requested currencies have valid rates
    valid_rates = True
    for currency in currencies:
        if currency not in cached_rates or cached_rates[currency] <= 0:
            plugin.log(f"Cache miss or invalid: {currency} rate is {cached_rates.get(currency, 'missing')}")
            valid_rates = False
        else:
            btc_value = cached_rates["btc"] / cached_rates[currency]
            if btc_value < 1e3 or btc_value > 1e10:  # Unrealistic: 1 BTC < 1K or > 10B fiat
                plugin.log(f"Cache invalid: {currency} rate gives {btc_value:,.2f} fiat/BTC")
                valid_rates = False

    if RATES_CACHE["timestamp"] + CACHE_TIMEOUT > current_time and valid_rates:
        plugin.log(f"Using cached currency rates: {cached_rates.keys()}")
        return cached_rates

    plugin.log("Cache invalid or expired, fetching new rates")
    rates = cached_rates.copy()

    # Try APIs in order: CoinGecko, CoinPaprika, CoinCap
    api_attempts = [
        (fetch_coingecko_rates, "CoinGecko"),
        (fetch_coinpaprika_rates, "CoinPaprika"),
        (fetch_coincap_rates, "CoinCap")
    ]
    for fetch_func, api_name in api_attempts:
        btc_rates = fetch_func(currencies)
        if btc_rates:
            for currency in currencies:
                if currency in btc_rates and btc_rates[currency] > 0:
                    rates[currency] = rates["btc"] / btc_rates[currency]  # msat per currency
                    btc_value = btc_rates[currency]  # fiat per BTC
                    plugin.log(f"Rate for {currency} from {api_name}: {rates[currency]:,.2f} msat ({btc_value:,.2f} {currency.upper()}/BTC)")
                else:
                    plugin.log(f"No valid rate for {currency} from {api_name}")
            if all(currency in btc_rates and btc_rates[currency] > 0 for currency in currencies):
                break  # All currencies fetched successfully
        else:
            plugin.log(f"{api_name} returned no valid rates")

    # Fallback to defaults for missing or invalid rates
    for currency in currencies:
        if currency not in rates or rates[currency] <= 0:
            if currency in CONVERSION_RATES:
                rates[currency] = CONVERSION_RATES[currency]
                btc_value = rates["btc"] / rates[currency]
                plugin.log(f"Using fallback for {currency}: {rates[currency]:,.2f} msat ({btc_value:,.2f} {currency.upper()}/BTC)")
            else:
                plugin.log(f"No fallback available for {currency}")
                rates[currency] = 0

    # Update cache
    RATES_CACHE["rates"] = rates
    RATES_CACHE["timestamp"] = current_time
    plugin.log(f"Updated currency rates: {rates}")
    return rates

def format_currency(amount_msat, currency, rates):
    """Convert msat to specified currency and format with commas for fiat."""
    if rates[currency] == 0:
        return f"0.00 {currency.upper()}"  # Handle invalid rates
    amount = amount_msat / rates[currency]
    if currency == "msats":
        return f"{amount:,.0f} {currency}"
    elif currency == "sats":
        return f"{amount:,.0f} {currency}"
    elif currency == "btc":
        return f"{amount:.8f} {currency}"
    else:
        return f"{amount:,.2f} {currency.upper()}"

def format_balance(amount_msat, rates, fiat_currencies):
    """Format balance in btc, sats, msats, and specified fiat currencies in order."""
    balance = OrderedDict()
    # Fixed order: btc, sats, msats
    balance["btc"] = format_currency(amount_msat, "btc", rates)
    balance["sats"] = format_currency(amount_msat, "sats", rates)
    balance["msats"] = format_currency(amount_msat, "msats", rates)
    # Add only requested fiat currencies
    for currency in fiat_currencies:
        if currency in rates and rates[currency] > 0:
            btc_value = rates["btc"] / rates[currency]
            if btc_value < 1e3 or btc_value > 1e10:  # Skip unrealistic rates
                plugin.log(f"Skipping {currency} balance: {btc_value:,.2f} fiat/BTC is invalid")
                continue
            balance[currency] = format_currency(amount_msat, currency, rates)
        else:
            plugin.log(f"Skipping {currency}: no valid rate available")
    return balance

def format_rates(rates, fiat_currencies, timestamp):
    """Format BTC to fiat currency rates with timestamp and cache status."""
    btc_rates = {}
    for currency in fiat_currencies:
        if currency in rates and rates[currency] > 0:
            btc_value = rates["btc"] / rates[currency]  # 1 BTC in fiat
            # Skip validation for CONVERSION_RATES to allow fallbacks
            if currency not in CONVERSION_RATES and (btc_value < 1e3 or btc_value > 1e10):  # Unrealistic rates
                plugin.log(f"Skipping {currency} rate: {btc_value:,.2f} fiat/BTC is invalid")
                btc_rates[currency] = "Rate invalid"
            else:
                btc_rates[currency] = f"{btc_value:,.2f} {currency.upper()}"
                plugin.log(f"Formatted rate for {currency}: {btc_rates[currency]}")
        else:
            btc_rates[currency] = "Rate unavailable"
    return {
        "rates": btc_rates,
        "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
        "cached": timestamp + CACHE_TIMEOUT > time.time()
    }

@plugin.method("nodebalance")
def node_balance(plugin, mode="total", currencies=""):
    """
    RPC method to display node balances or rates based on mode.
    Modes: total, onchain, channels, channel-details, rate.
    All balance modes include btc, sats, msats, and user-specified currencies.
    Rate mode shows BTC to fiat rates.
    Currencies: comma-separated list (e.g., usd,mxn,eur); defaults to usd,mxn if empty.
    """
    try:
        # Validate mode
        valid_modes = ["total", "onchain", "channels", "channel-details", "rate"]
        if mode not in valid_modes:
            # Check if mode is actually a currency (e.g., 'eur')
            if currencies == "":
                currencies = mode
                mode = "total"
            else:
                raise Exception(f"Invalid mode: {mode}. Use: {', '.join(valid_modes)}")

        # Parse currencies
        fiat_currencies = [c.strip().lower() for c in currencies.split(",") if c.strip()]
        # Use default currencies only if none specified
        if not fiat_currencies:
            fiat_currencies = DEFAULT_CURRENCIES
        plugin.log(f"Parsed fiat currencies: {fiat_currencies}")

        # Check for invalid currencies in rate mode
        if mode == "rate":
            invalid_currencies = [c for c in fiat_currencies if c not in VALID_CURRENCIES]
            if invalid_currencies:
                plugin.log(f"Invalid currencies detected: {invalid_currencies}")
                rates_response = {
                    "rates": {c: "Rate unavailable" if c in invalid_currencies else "Rate unavailable" for c in fiat_currencies},
                    "timestamp": datetime.fromtimestamp(time.time()).isoformat(),
                    "cached": False
                }
                return rates_response

        # Fetch currency rates
        rates = get_currency_rates(fiat_currencies)
        plugin.log(f"Rates available for: {rates.keys()}")

        # Handle rate mode
        if mode == "rate":
            return format_rates(rates, fiat_currencies, RATES_CACHE["timestamp"])

        # Fetch listfunds data for balance modes
        funds = plugin.rpc.listfunds()
        plugin.log(f"listfunds output: {json.dumps(funds, indent=2)}")

        # Calculate on-chain balance
        onchain_balance_msat = sum(output["amount_msat"] for output in funds["outputs"] if output["status"] == "confirmed" and not output["reserved"])
        plugin.log(f"On-chain balance: {onchain_balance_msat} msat")

        # Calculate channel balances and details
        total_channel_balance_msat = 0
        channel_details = []
        for channel in funds["channels"]:
            if channel["state"] == "CHANNELD_NORMAL" and channel["connected"]:
                our_msat = channel["our_amount_msat"]
                total_msat = channel["amount_msat"]
                outbound_msat = our_msat
                inbound_msat = total_msat - our_msat
                total_channel_balance_msat += our_msat
                channel_details.append({
                    "peer_id": channel["peer_id"][:10] + "...",
                    "short_channel_id": channel.get("short_channel_id", "N/A"),
                    "outbound_msat": outbound_msat,
                    "inbound_msat": inbound_msat
                })
        plugin.log(f"Total channel balance: {total_channel_balance_msat} msat")

        # Prepare output based on mode
        if mode == "onchain":
            return {
                "onchain_balance": format_balance(onchain_balance_msat, rates, fiat_currencies)
            }
        elif mode == "channels":
            return {
                "channel_balance": format_balance(total_channel_balance_msat, rates, fiat_currencies)
            }
        elif mode == "channel-details":
            return {
                "channels": [
                    {
                        "peer_id": ch["peer_id"],
                        "short_channel_id": ch["short_channel_id"],
                        "outbound_capacity": format_currency(ch["outbound_msat"], "msats", rates),
                        "inbound_capacity": format_currency(ch["inbound_msat"], "msats", rates),
                        "outbound_balance": format_balance(ch["outbound_msat"], rates, fiat_currencies),
                        "inbound_balance": format_balance(ch["inbound_msat"], rates, fiat_currencies)
                    } for ch in channel_details
                ]
            }
        else:  # mode == "total"
            total_balance_msat = onchain_balance_msat + total_channel_balance_msat
            return {
                "total_balance": format_balance(total_balance_msat, rates, fiat_currencies)
            }

    except Exception as e:
        plugin.log(f"Error in nodebalance: {str(e)}")
        raise Exception(f"Failed to retrieve balance: {str(e)}")

plugin.add_option("nodebalance-mode", "total", "Default output mode: total, onchain, channels, channel-details, rate")
plugin.add_option("nodebalance-currencies", "", "Default currencies: comma-separated (e.g., usd,mxn,eur); empty for usd,mxn")

if __name__ == "__main__":
    plugin.run()
    