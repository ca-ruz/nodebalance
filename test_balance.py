import os
from pyln.testing.fixtures import *  # noqa: F403
from pyln.testing.utils import sync_blockheight

plugin = {'plugin': os.path.join(os.path.dirname(__file__), "nodebalance.py")}

def test_nodebalance_basic(node_factory):
    l1 = node_factory.get_nodes(1, opts=plugin)[0]
    bitcoind = l1.bitcoin

    addr = l1.rpc.newaddr()['bech32']
    bitcoind.rpc.sendtoaddress(addr, 1)
    bitcoind.generate_block(6)
    sync_blockheight(bitcoind, [l1])

    l2 = node_factory.get_nodes(1)[0]
    l1.rpc.connect(l2.info['id'], 'localhost', l2.port)
    l1.rpc.fundchannel(l2.info['id'], 100000)
    bitcoind.generate_block(6)
    sync_blockheight(bitcoind, [l1, l2])

    # Run nodebalance and check results
    bal = l1.rpc.nodebalance()

    # Assert the 'total_balance' key exists
    assert "total_balance" in bal, "Missing total_balance"
    
    # Check each key inside total_balance for existence and non-empty value
    total_balance = bal["total_balance"]
    
    keys_to_check = ["btc", "sats", "msats", "usd", "mxn"]
    for key in keys_to_check:
        assert key in total_balance, f"Missing {key} in total_balance"
        assert total_balance[key], f"Empty value for {key} in total_balance"
        
        # For specific keys (like sats), you can also assert they have a valid numeric format:
        if key == "sats":
            sats_str = total_balance[key].replace(",", "").replace(" sats", "")
            sats = int(sats_str)
            assert sats > 0, f"Expected positive value for {key}"

    # Check if 'sats' value is non-zero
    sats = int(total_balance["sats"].replace(",", "").replace(" sats", ""))
    assert sats > 0, "Expected non-zero balance for sats"

if __name__ == "__main__":
    from pyln.testing.fixtures import setup_node_factory
    node_factory = setup_node_factory()
    test_nodebalance_basic(node_factory)
