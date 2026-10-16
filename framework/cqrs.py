"""CQRS: command side (writes) and query side (reads) are separated.
Writes update the write store and project into a read-optimized view.
Reads never touch the write store."""
import json, os, tempfile


class WriteStore:
    def __init__(self, path):
        self.path = path
        if not os.path.exists(path):
            self._write({"orders": {}})

    def _read(self):
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(self.path), suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp, self.path)

    def save_order(self, order):
        db = self._read()
        db["orders"][order["order_id"]] = order
        self._write(db)

    def get_order(self, order_id):
        return self._read()["orders"].get(order_id)


class ReadStore:
    """Read-optimized projection. Rebuilt from write store."""
    def __init__(self):
        self.orders = {}        # order_id -> flattened view
        self.user_orders = {}   # user_id -> [order_id]

    def project(self, order):
        oid = order["order_id"]
        self.orders[oid] = {
            "order_id": oid, "user_id": order["user_id"],
            "amount": order["amount"], "status": order["status"],
        }
        self.user_orders.setdefault(order["user_id"], []).append(oid)

    def list_user_orders(self, user_id):
        return [self.orders[oid] for oid in self.user_orders.get(user_id, [])]

    def get_order(self, order_id):
        return self.orders.get(order_id)


class OrderCommandService:
    def __init__(self, write_store: WriteStore, read_store: ReadStore):
        self.ws = write_store
        self.rs = read_store

    def create_order(self, order_id, user_id, amount):
        order = {"order_id": order_id, "user_id": user_id, "amount": amount, "status": "CREATED"}
        self.ws.save_order(order)
        self.rs.project(order)   # sync projection to read side
        return order

    def pay_order(self, order_id):
        order = self.ws.get_order(order_id)
        order["status"] = "PAID"
        self.ws.save_order(order)
        self.rs.project(order)
        return order


class OrderQueryService:
    def __init__(self, read_store: ReadStore):
        self.rs = read_store

    def order_detail(self, order_id):
        return self.rs.get_order(order_id)

    def orders_of_user(self, user_id):
        return self.rs.list_user_orders(user_id)
