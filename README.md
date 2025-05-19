# Nodebalance Plugin

A Core Lightning plugin to retrieve and display on-chain and channel balances, with optional fiat currency conversion using external APIs (CoinGecko, CoinPaprika, CoinCap).

## Prerequisites

- Python 3.8+
- Core Lightning 24.11+
- Internet access for fiat currency conversion

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd nodebalance
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
# Install plugin dependencies
pip install -r requirements.txt

# Install test dependencies (optional)
pip install -r requirements-dev.txt
```

## Usage

1. Ensure Core Lightning is running.

2. Start the plugin:
```bash
lightning-cli plugin start $PWD/nodebalance.py
```

3. Check balances or rates using the `nodebalance` command with optional modes and currencies.

### Examples

1. **Total Balance** (default mode, default currencies: USD, MXN):
```bash
lightning-cli nodebalance
```
Output:
```json
{
  "total_balance": {
    "btc": "0.00200000 btc",
    "sats": "200000 sats",
    "msats": "200000000 msats",
    "usd": "200.00 USD",
    "mxn": "4000.00 MXN"
  }
}
```

2. **On-chain Balance** with specific currencies:
```bash
lightning-cli nodebalance onchain usd,eur
```
Output:
```json
{
  "onchain_balance": {
    "btc": "0.00197999 btc",
    "sats": "197999 sats",
    "msats": "197999000 msats",
    "usd": "197.99 USD",
    "eur": "183.68 EUR"
  }
}
```

3. **Channel Balances**:
```bash
lightning-cli nodebalance channels
```
Output:
```json
{
  "channel_balance": {
    "btc": "0.00002000 btc",
    "sats": "2000 sats",
    "msats": "2000000 msats",
    "usd": "2.00 USD",
    "mxn": "40.00 MXN"
  }
}
```

4. **Channel Details**:
```bash
lightning-cli nodebalance channel-details usd
```
Output:
```json
{
  "channels": [
    {
      "peer_id": "02f6725f9c1...",
      "short_channel_id": "123x456x7",
      "outbound_capacity": "1000000 msats",
      "inbound_capacity": "9000000 msats",
      "outbound_balance": {
        "btc": "0.00001000 btc",
        "sats": "1000 sats",
        "msats": "1000000 msats",
        "usd": "1.00 USD"
      },
      "inbound_balance": {
        "btc": "0.00009000 btc",
        "sats": "9000 sats",
        "msats": "9000000 msats",
        "usd": "9.00 USD"
      }
    }
  ]
}
```

5. **Fiat Rates**:
```bash
lightning-cli nodebalance rate usd,mxn,eur
```
Output:
```json
{
  "rates": {
    "usd": "100000.00 USD",
    "mxn": "2000000.00 MXN",
    "eur": "92857.14 EUR"
  },
  "timestamp": "2025-05-13T14:35:00",
  "cached": true
}
```

## Supported Currencies

The plugin supports the following fiat currencies for conversion (case-insensitive):

- AED, ARS, AUD, BDT, BHD, BMD, BRL, CAD, CHF, CLP, CNY, CZK, DKK, EUR, GBP, HKD, HUF, IDR, ILS, INR, JPY, KRW, KWD, LKR, MMK, MXN, MYR, NGN, NOK, NZD, PHP, PKR, PLN, RUB, SAR, SEK, SGD, THB, TRY, TWD, UAH, USD, VEF, VND, XAG, XAU, XDR, ZAR

Specify currencies as a comma-separated list (e.g., `usd,mxn,eur`). Invalid currencies will return "Rate unavailable" in rate mode.

## Running Tests

The test suite uses Core Lightning’s test framework and requires a regtest environment. Run the following commands inside the plugin directory.

1. To run all tests:
```bash
pytest -vs
```

2. To run an individual test:
```bash
pytest -vs <name_of_the_test_file.py>
```

## Manual Testing in Regtest

1. Start the regtest environment:
```bash
source ~/code/lightning/contrib/startup_regtest.sh
start_ln
```

2. Fund the nodes:
```bash
fund_nodes
```

3. Start the plugin (from the plugin directory):
```bash
l1-cli plugin start $PWD/nodebalance.py
```

4. Check balances or rates:
```bash
l1-cli nodebalance total usd,eur
```
or
```bash
l1-cli nodebalance rate usd,mxn
```

## Plugin Configuration

The plugin accepts the following configuration options:

- `nodebalance-mode`: Default output mode (`total`, `onchain`, `channels`, `channel-details`, `rate`). Default: `total`.
- `nodebalance-currencies`: Comma-separated fiat currencies (e.g., `usd,mxn,eur`). Default: `usd,mxn`.
- `nodebalance-api`: Preferred API for fiat currency rates (`coingecko`, `coinpaprika`, `coincap`, or `auto`). Default: `auto` (tries CoinGecko, then CoinPaprika, then CoinCap).

Example:
```bash
lightningd --plugin=$PWD/nodebalance.py --nodebalance-mode=channels --nodebalance-currencies=usd,eur --nodebalance-api=coingecko
```

## Notes

- The plugin fetches fiat currency rates from external APIs (CoinGecko, CoinPaprika, CoinCap) and caches them for 1 hour to reduce API calls.
- If an API fails or a currency is unsupported, the plugin falls back to the next API or uses default rates (e.g., 1 BTC ≈ 100,000 USD, 2,000,000 MXN).
- Rates are validated to ensure realistic values (1 BTC between 1,000 and 10,000,000,000 fiat). Invalid rates are skipped.

## Contributing

1. Fork the repository.
2. Create a new branch for your feature.
3. Make your changes.
4. Run the test suite to ensure everything works.
5. Submit a pull request.
