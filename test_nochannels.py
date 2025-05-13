import os
from pyln.testing.fixtures import *  # noqa: F403
from pyln.testing.utils import sync_blockheight

plugin = {'plugin': os.path.join(os.path.dirname(__file__), "nodebalance.py")}

def test_nodebalance_no_channels(node_factory):
    """
    Node has no channels at all. Channel balance should be 0.
    """
    l1 = node_factory.get_nodes(1, opts=plugin)[0]
    bitcoind = l1.bitcoin

    addr = l1.rpc.newaddr()['bech32']
    bitcoind.rpc.sendtoaddress(addr, 1)
    bitcoind.generate_block(6)
    sync_blockheight(bitcoind, [l1])

    bal = l1.rpc.nodebalance()
    
    # Check if the total_balance contains msats and channel_balance is 0
    assert "total_balance" in bal
    assert "msats" in bal["total_balance"]
    
    # Convert msats to integer and check it's greater than 0
    onchain_balance_msat = int(bal["total_balance"]["msats"].replace(",", "").replace(" msats", ""))
    assert onchain_balance_msat > 0  # On-chain balance should be greater than 0
    
    # Ensure that the channel_balance_msat is either not present or 0 (since no channels exist)
    assert "channel_balance_msat" not in bal or bal["channel_balance_msat"] == 0

if __name__ == "__main__":
    from pyln.testing.fixtures import setup_node_factory
    node_factory = setup_node_factory()
    test_nodebalance_no_channels(node_factory)
