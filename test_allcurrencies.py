import os
from pyln.testing.fixtures import *  # noqa: F403
from unittest.mock import patch
from pyln.testing.utils import sync_blockheight

plugin = {'plugin': os.path.join(os.path.dirname(__file__), "nodebalance.py")}

def test_nodebalance_all_currencies(node_factory):
    """
    Test the nodebalance plugin's -rate mode for all currencies from CoinGecko API.
    """
    # Mock CoinGecko's supported currencies endpoint
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = ["usd", "eur", "mxn", "gbp", "vnd"]

        # Set up a node with the plugin
        l1 = node_factory.get_nodes(1, opts=plugin)[0]
        bitcoind = l1.bitcoin

        # Fund the node with 0.1 BTC
        addr = l1.rpc.newaddr()['bech32']
        bitcoind.rpc.sendtoaddress(addr, 0.1)
        bitcoind.generate_block(6)
        sync_blockheight(bitcoind, [l1])

        # Test each currency
        for curr in mock_get.return_value.json.return_value:
            bal = l1.rpc.nodebalance(mode="rate", currencies=curr.upper())  # CoinGecko uses lowercase, plugin may expect uppercase
            assert "rates" in bal, "Missing rates"
            assert curr.lower() in bal["rates"], f"Rate for {curr.upper()} missing"
            assert isinstance(bal["rates"][curr.lower()], str), f"Rate for {curr.upper()} should be a string"
            assert len(bal["rates"][curr.lower()]) > 0, f"Rate for {curr.upper()} should not be empty"

if __name__ == "__main__":
    from pyln.testing.fixtures import setup_node_factory
    node_factory = setup_node_factory()
    test_nodebalance_all_currencies(node_factory)
