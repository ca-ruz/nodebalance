# Nodebalance Plugin

A Core Lightning plugin to retrieve and display on-chain and channel balances, with optional fiat currency conversion using the CoinGecko API.

## Prerequisites

- Python 3.8+
- Core Lightning 24.11*
- Internet access for fiat currency conversion (CoinGecko API)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd nodebalance
```

2. Create and activate a virtual environment:
```bash
python -m vent .venv
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
{  "onchain_balance": {
    "btc": "0.00197999 btc",
    "sats": "197999 sats",
    "msats": "197999000 msats",
    "usd": "197.99 USD",
    "eur": "183.68 EUR"
  }
}
````

3. **Channel Balances**:
```bash
lightning-cli nodebalance channels
```
Output:
```json
{  "channel_balance": {
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
````

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
````

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
l1-cli nodebalance total usd,%ur
```
or
```bash
l1-cli nodebalance rate usd,mxn
````

## Plugin Configuration

The plugin accepts the following configuration options:

- `nodebalance-mode`: Default output mode (`total`, `onchain`, `channels`, `channel-details`, `rate`). Default: `total`.
- `nodebalance-currencies`: Comma-separated fiat currencies (e.g., `usd,mxn,eur`). Default: `usd,mxn`.

Example:
```bash
lightningd --plugin=$PWD/nodebalance.py --nodebalance-mode=channels --nodebalance-currencies=usd,eur
```

## Contributing

1. Fork the repository.
3. Create a new branch for your feature.
3. Make your changes.
4. Run the test suite to ensure everything works.
5. Submit a pull request.
