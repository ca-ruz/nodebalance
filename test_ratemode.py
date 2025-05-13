import os
from pyln.testing.fixtures import *  # noqa: F403
from pyln.testing.utils import sync_blockheight

plugin = {'plugin': os.path.join(os.path.dirname(__file__), "nodebalance.py")}

def test_nodebalance_rate_mode(node_factory):
    """
    Test the nodebalance plugin's -rate mode with EUR to ensure correct fiat conversion.
    """
    l1 = node_factory.get_nodes(1, opts=plugin)[0]
    bitcoind = l1.bitcoin

    # Fund the node with 0.5 BTC
    addr = l1.rpc.newaddr()['bech32']
    bitcoind.rpc.sendtoaddress(addr, 0.5)
    bitcoind.generate_block(6)
    sync_blockheight(bitcoind, [l1])

    # Run nodebalance with -rate EUR
    bal = l1.rpc.nodebalance(mode="rate", currencies="eur")

    # Check the structure of the result
    assert "rates" in bal, "Missing rates in response"
    assert "eur" in bal["rates"], "EUR rate missing"
    assert "timestamp" in bal, "Missing timestamp"
    assert "cached" in bal, "Missing cache status"

if __name__ == "__main__":
    from pyln.testing.fixtures import setup_node_factory
    node_factory = setup_node_factory()
    test_nodebalance_rate_mode(node_factory)
