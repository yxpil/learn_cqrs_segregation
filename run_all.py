"""Demo: CQRS - writes go to command side, reads go to query side (projection)."""
import os, shutil
from framework.cqrs import WriteStore, ReadStore, OrderCommandService, OrderQueryService

DATA = os.path.join(os.path.dirname(__file__), "data")


def main():
    if os.path.exists(DATA):
        shutil.rmtree(DATA)
    os.makedirs(DATA, exist_ok=True)

    ws = WriteStore(os.path.join(DATA, "write_store.json"))
    rs = ReadStore()
    cmd = OrderCommandService(ws, rs)
    qry = OrderQueryService(rs)

    print("--- Case 1: write commands update write store + project to read side ---")
    cmd.create_order("o_1", "alice", 199.5)
    cmd.create_order("o_2", "alice", 49.0)
    cmd.create_order("o_3", "bob", 120.0)
    print("  created 3 orders")

    print("\n--- Case 2: reads go to query side (read model) ---")
    print("  alice orders:", qry.orders_of_user("alice"))
    print("  bob orders:", qry.orders_of_user("bob"))
    print("  order o_1 detail:", qry.order_detail("o_1"))

    print("\n--- Case 3: pay command updates both stores, read reflects new status ---")
    cmd.pay_order("o_1")
    print("  o_1 after pay:", qry.order_detail("o_1"))

    print("\n== all cases done ==")


if __name__ == "__main__":
    main()
