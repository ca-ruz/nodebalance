import os
from pyln.testing.fixtures import *  # noqa: F403
from pyln.testing.utils import sync_blockheight

plugin = {'plugin': os.path.join(os.path.dirname(__file__), "nodebalance.py")}

def test_nodebalance_invalid_currency(node_factory):
    """
    Test that nodebalance returns 'Rate unavailable' for an invalid currency.
    """
    l1 = node_factory.get_nodes(1, opts=plugin)[0]

    # Check invalid currency XYZ returns Rate unavailable
    response = l1.rpc.nodebalance(mode="rate", currencies="XYZ")
    assert "rates" in response
    assert "xyz" in response["rates"]  # lowercase key
    assert response["rates"]["xyz"] == "Rate unavailable"

if __name__ == "__main__":
    from pyln.testing.fixtures import setup_node_factory
    node_factory = setup_node_factory()
    test_nodebalance_invalid_currency(node_factory)
    