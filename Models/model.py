"""
Order book implementation.

Design:
- Each price level is a node in an AVL tree (self-balancing BST), keyed by price.
- Each price-level node holds a FIFO queue (doubly linked list) of orders at that price,
  giving price-time priority.
- When a price level's queue empties, the node is deleted ("unloaded") from the tree.
- A top-level dict maps stock symbol -> {"buy": OrderTree, "sell": OrderTree}.
"""
from typing import TypeVar
from datetime import datetime
from enum import Enum

X = TypeVar("X")
Y = TypeVar("Y")

class OrderStatus(Enum):
    NEW = "new"                        # resting, untouched
    PARTIALLY_FILLED = "partially_filled"   # some quantity traded, remainder still resting
    FILLED = "filled"                  # fully traded
    CANCELLED = "cancelled"            # cancelled by user, or IOC remainder, or unwound
    REJECTED = "rejected"              # never entered the book at all


class OrderType(Enum):
    GTC = "GTC"   # Good-Til-Cancelled: unmatched remainder rests in the book
    IOC = "IOC"   # Immediate-Or-Cancel: match what you can right now, cancel the rest
    FOK = "FOK"   # Fill-Or-Kill: must fill completely right now, or nothing trades at all


class Orders:
    """Details about a single order."""

    def __init__(self, id: int, user_id: int, type: str, price: float, stock: str,
                 quantity: int, order_type: OrderType = OrderType.GTC):
        self._id = id
        self._user_id = user_id
        self._stock = stock
        self._type = type          # "buy" / "sell"
        self._price = price
        self._quantity = quantity          
        self.original_quantity = quantity  
        self.order_type = order_type
        self.status = OrderStatus.NEW
        self.time = datetime.now()

    def __repr__(self):
        return (f"Order(id={self._id}, {self._type} {self._quantity}/"
                f"{self.original_quantity}@{self._price}, {self.status.value})")


class OrderQueueNode:
    """Node in the doubly linked FIFO queue for a single price level."""

    def __init__(self, order: Orders):
        self._order = order
        self._next: "OrderQueueNode | None" = None
        self._prev: "OrderQueueNode | None" = None

    def setPrev(self, node: "OrderQueueNode | None") -> None:
        self._prev = node

    def setNext(self, node: "OrderQueueNode | None") -> None:
        self._next = node         

    def removeSelf(self):
        if self._next:
            self._next._prev = self._prev
        if self._prev:
            self._prev._next = self._next


class OrderQueue:
    """FIFO queue of orders sitting at one price level."""

    def __init__(self):
        self._head: "OrderQueueNode | None" = None
        self._tail: "OrderQueueNode | None" = None
        self._size = 0
        self._total_qty = 0        # cached sum of remaining quantity across the queue

    def is_empty(self) -> bool:
        return self._head is None         

    def __len__(self):
        return self._size

    def pop(self) -> "OrderQueueNode | None":
        """Pop the oldest order (FIFO) off the front of the queue."""
        if not self._head:
            return None

        x = self._head
        self._head = self._head._next

        if self._head:                     
            self._head._prev = None
        else:
            self._tail = None              
        x._next = None
        x._prev = None
        self._size -= 1
        self._total_qty -= x._order._quantity
        return x

    def append(self, node: OrderQueueNode) -> None:
        if not self._head:
            self._head = node
            self._tail = node
            self._size += 1
            self._total_qty += node._order._quantity
            return                          
                                            

        self._tail.setNext(node)
        node.setPrev(self._tail)
        self._tail = node
        self._size += 1
        self._total_qty += node._order._quantity

    def peek(self) -> "OrderQueueNode | None":
        """Look at the oldest order without removing it (needed for partial fills)."""
        return self._head

    def remove(self, node: OrderQueueNode) -> None:
        """Remove a specific node from anywhere in the queue (needed for cancel-by-id)."""
        if node is self._head:
            self._head = node._next
        if node is self._tail:
            self._tail = node._prev
        if node._prev:
            node._prev._next = node._next
        if node._next:
            node._next._prev = node._prev
        node._next = None
        node._prev = None
        self._size -= 1
        self._total_qty -= node._order._quantity

    def adjust_total(self, delta: int) -> None:
        """
        Keep the cached total in sync when an order's quantity changes IN PLACE
        (a partial fill) without the order being appended, popped, or removed.
        delta is negative for a fill (quantity going down).
        """
        self._total_qty += delta

    def total_quantity(self) -> int:
        """Sum of remaining quantity across every order in this queue. O(1): cached."""
        return self._total_qty


class TreeNode:
    """A price level in the AVL tree. Holds the queue of orders resting at that price."""

    def __init__(self, key: float, queue: OrderQueue):
        self.key = key                      # price
        self.queue = queue                  # OrderQueue of OrderQueueNode at this price
        self.left: "TreeNode | None" = None
        self.right: "TreeNode | None" = None
        self.height = 1
        self.subtree_qty = 0                # this level's queue total + left's + right's


class OrderTree:
    """Self-balancing AVL tree of price levels (one side of the book: all buys or all sells)."""

    def __init__(self):
        self.root: "TreeNode | None" = None
        self._node_by_price: dict[float, TreeNode] = {}   # price -> TreeNode, O(1) lookup

    # ---- height / balance helpers ----
    def get_height(self, node: "TreeNode | None") -> int:
        return node.height if node else 0

    def get_balance(self, node: "TreeNode | None") -> int:
        return self.get_height(node.left) - self.get_height(node.right) if node else 0

    def _qty(self, node: "TreeNode | None") -> int:
        return node.subtree_qty if node else 0

    def _recompute(self, node: TreeNode) -> None:
        """Refresh both cached aggregates for a single node from its (already-correct) children."""
        node.height = 1 + max(self.get_height(node.left), self.get_height(node.right))
        node.subtree_qty = node.queue.total_quantity() + self._qty(node.left) + self._qty(node.right)

    def _rotate_right(self, z: TreeNode) -> TreeNode:
        y = z.left
        T2 = y.right
        y.right = z
        z.left = T2
        self._recompute(z)
        self._recompute(y)
        return y

    def _rotate_left(self, z: TreeNode) -> TreeNode:
        y = z.right
        T2 = y.left
        y.left = z
        z.right = T2
        self._recompute(z)
        self._recompute(y)
        return y

    def _rebalance(self, node: TreeNode, key: float) -> TreeNode:
        """Insert-time rebalance: safe to use the just-inserted key to pick the rotation,
        since inserting one key grows exactly one subtree by exactly one level."""
        balance = self.get_balance(node)
        if balance > 1 and key < node.left.key:
            return self._rotate_right(node)
        if balance < -1 and key > node.right.key:
            return self._rotate_left(node)
        if balance > 1 and key > node.left.key:
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        if balance < -1 and key < node.right.key:
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)
        return node

    def _rebalance_after_delete(self, node: TreeNode) -> TreeNode:
        """
        Delete-time rebalance: the removed key does NOT reliably indicate which side
        is heavy (unlike insert), so this must look at the CHILD's balance factor
        instead. Using the key-based _rebalance() here is a real bug -- it can pick
        a rotation whose target child is None and crash.
        """
        balance = self.get_balance(node)
        if balance > 1:
            if self.get_balance(node.left) >= 0:
                return self._rotate_right(node)              # LL
            node.left = self._rotate_left(node.left)          # LR
            return self._rotate_right(node)
        if balance < -1:
            if self.get_balance(node.right) <= 0:
                return self._rotate_left(node)                # RR
            node.right = self._rotate_right(node.right)        # RL
            return self._rotate_left(node)
        return node

    # ---- find (get the queue at a price, without modifying the tree) ----
    def find(self, price: float) -> "TreeNode | None":
        return self._node_by_price.get(price)         # O(1) instead of walking the tree

    # ---- insert an order at its price level, creating the level if needed ----
    def add_order(self, order: Orders) -> OrderQueueNode:
        qnode = OrderQueueNode(order)
        existing = self.find(order._price)             # O(1) dict lookup
        if existing:
            existing.queue.append(qnode)                # O(1): price level already exists
            self.root = self._refresh_qty_path(self.root, order._price)
        else:
            self.root = self._insert(self.root, order._price, qnode)   # O(log n): genuinely new level
        return qnode

    def _insert(self, root: "TreeNode | None", key: float, qnode: OrderQueueNode) -> TreeNode:
        if not root:
            new_node = TreeNode(key, OrderQueue())
            new_node.queue.append(qnode)
            new_node.subtree_qty = new_node.queue.total_quantity()
            self._node_by_price[key] = new_node         # register the new level
            return new_node

        if key < root.key:
            root.left = self._insert(root.left, key, qnode)
        elif key > root.key:
            root.right = self._insert(root.right, key, qnode)
        else:
            root.queue.append(qnode)
            self._recompute(root)
            return root

        self._recompute(root)
        return self._rebalance(root, key)

    # ---- pop the oldest order at the best price, unloading the level if it empties ----
    def pop_best(self, best_is_min: bool) -> "tuple[float, OrderQueueNode] | None":
        """
        best_is_min=True  -> best price is the minimum key (typical for the sell/ask side)
        best_is_min=False -> best price is the maximum key (typical for the buy/bid side)
        """
        node = self._find_extreme(self.root, go_left=best_is_min)
        if node is None:
            return None
        price = node.key
        qnode = node.queue.pop()
        if node.queue.is_empty():
            self.delete(price)             # unload: remove empty price level from tree
        return price, qnode

    def _find_extreme(self, node: "TreeNode | None", go_left: bool) -> "TreeNode | None":
        if node is None:
            return None
        while (go_left and node.left) or (not go_left and node.right):
            node = node.left if go_left else node.right
        return node

    def peek_best(self, best_is_min: bool) -> "TreeNode | None":
        """Look at the best price level's node without popping an order or unloading it."""
        return self._find_extreme(self.root, go_left=best_is_min)

    def unload_if_empty(self, price: float) -> None:
        """Remove a price level from the tree if its queue has drained to empty."""
        node = self.find(price)
        if node is not None and node.queue.is_empty():
            self.delete(price)

    def cancel_order(self, price: float, qnode: OrderQueueNode) -> bool:
        """Remove one specific resting order from its price level (used by cancel-by-id)."""
        node = self.find(price)
        if node is None:
            return False
        node.queue.remove(qnode)
        self.root = self._refresh_qty_path(self.root, price)
        self.unload_if_empty(price)
        return True

    def refresh_quantity(self, price: float) -> None:
        """
        Recompute cached subtree_qty aggregates along the path to `price`, without
        touching tree shape. Call this after a queue's total quantity changes in place
        (a partial fill) but no node was inserted or removed.
        """
        self.root = self._refresh_qty_path(self.root, price)

    def _refresh_qty_path(self, node: "TreeNode | None", price: float) -> "TreeNode | None":
        if node is None:
            return None
        if price < node.key:
            node.left = self._refresh_qty_path(node.left, price)
        elif price > node.key:
            node.right = self._refresh_qty_path(node.right, price)
        # else: price == node.key, this is the level whose queue just changed -- nothing to recurse into
        node.subtree_qty = node.queue.total_quantity() + self._qty(node.left) + self._qty(node.right)
        return node

    def matchable_quantity(self, order: Orders) -> int:
        """
        How much of `order` could trade right now against this tree, without
        actually mutating anything. O(log n): at every node, one whole side of the
        tree is either fully included (read its cached subtree_qty in O(1)) or fully
        excluded, based on the BST ordering -- so only a single path is ever walked,
        never both children.
        """
        def walk(node: "TreeNode | None") -> int:
            if node is None:
                return 0
            if order._type == "buy":
                if node.key <= order._price:
                    # this node and its entire left subtree qualify -- take left's
                    # cached total for free, only keep checking further right
                    return self._qty(node.left) + node.queue.total_quantity() + walk(node.right)
                else:
                    # this node (and everything right of it) is too expensive -- skip right entirely
                    return walk(node.left)
            else:  # sell: mirror image -- right subtree is the "fully included" side
                if node.key >= order._price:
                    return self._qty(node.right) + node.queue.total_quantity() + walk(node.left)
                else:
                    return walk(node.right)

        return walk(self.root)

    # ---- delete a price level entirely (used once its queue is empty) ----
    def delete(self, price: float) -> None:
        self.root = self._delete(self.root, price)

    def _delete(self, root: "TreeNode | None", key: float) -> "TreeNode | None":
        if not root:
            return root

        if key < root.key:
            root.left = self._delete(root.left, key)
        elif key > root.key:
            root.right = self._delete(root.right, key)
        else:
            if root.left is None:
                del self._node_by_price[root.key]      # this node is leaving the tree entirely
                return root.right
            if root.right is None:
                del self._node_by_price[root.key]
                return root.left

            # Two children: we don't remove `root` -- we REPURPOSE it to hold the
            # successor's key/queue, then delete the successor node from the right
            # subtree. That means the dict needs two fixes, done AFTER the recursive
            # delete (which will itself clean up the successor's old dict entry):
            #   1. root's original price no longer has a node -> drop it
            #   2. the successor's price is now served by `root`, not the old node -> repoint it
            successor = self._find_extreme(root.right, go_left=True)
            old_key = root.key
            new_key = successor.key
            root.key = new_key
            root.queue = successor.queue
            root.right = self._delete(root.right, new_key)   # removes the old successor node + its dict entry
            del self._node_by_price[old_key]
            self._node_by_price[new_key] = root

        self._recompute(root)
        return self._rebalance_after_delete(root)

    def inorder(self, root: "TreeNode | None" = "__self__") -> list[float]:
        if root == "__self__":
            root = self.root
        if not root:
            return []
        return self.inorder(root.left) + [root.key] + self.inorder(root.right)


class OrderBookManager:
    """Top-level registry: stock symbol -> {"buy": OrderTree, "sell": OrderTree}."""

    def __init__(self, book: dict[str, dict[str, OrderTree]],price_band_pct: float = 10.0):
        self.books: dict[str, dict[str, OrderTree]] = book
        self.last_trade_price: dict[str, float] = {}
        self.price_band_pct = price_band_pct     # reject orders more than this % from reference
        self._resting_index: dict[int, dict] = {}  # order_id -> {symbol, side, price, qnode, order}
        self._listeners = []                        # callbacks: fn(order, event, detail)

    def on_event(self, callback) -> None:
        """Register a callback: callback(order, event: str, detail: dict) -> None.
        Fired synchronously the instant each fill/reject/cancel happens -- never batched."""
        self._listeners.append(callback)

    def _notify(self, order: Orders, event: str, detail: dict) -> None:
        for cb in self._listeners:
            cb(order, event, detail)

    def _get_book(self, symbol: str) -> dict[str, OrderTree]:
        if symbol not in self.books:
            self.books[symbol] = {"buy": OrderTree(), "sell": OrderTree()}
        return self.books[symbol]

    # ---- reference price for the price-band check ----
    def _reference_price(self, symbol: str) -> "float | None":
        book = self.books.get(symbol)
        if symbol in self.last_trade_price:
            return self.last_trade_price[symbol]
        if book:
            best_bid = book["buy"].peek_best(best_is_min=False)
            best_ask = book["sell"].peek_best(best_is_min=True)
            if best_bid and best_ask:
                return (best_bid.key + best_ask.key) / 2
            if best_bid:
                return best_bid.key
            if best_ask:
                return best_ask.key
        return None   # no reference yet (first order for this symbol) -> nothing to check against

    def _within_price_band(self, order: Orders) -> bool:
        ref = self._reference_price(order._stock)
        if ref is None:
            return True
        deviation_pct = abs(order._price - ref) / ref * 100
        return deviation_pct <= self.price_band_pct

    # ---- submission ----
    def submit(self, order: Orders) -> list[dict]:
        """
        Pre-trade check -> match -> handle remainder per order_type.
        Every fill fires a notification the instant it happens; nothing is held back
        until the whole order finishes (it might never fully finish for a GTC order).
        """
        if not self._within_price_band(order):
            order.status = OrderStatus.REJECTED
            ref = self._reference_price(order._stock)
            self._notify(order, "rejected", {
                "reason": "price_band",
                "reference_price": ref,
                "order_price": order._price,
                "band_pct": self.price_band_pct,
            })
            return []

        if order.order_type == OrderType.FOK:
            book = self._get_book(order._stock)
            opposite_tree = book["sell" if order._type == "buy" else "buy"]
            if opposite_tree.matchable_quantity(order) < order._quantity:
                order.status = OrderStatus.REJECTED
                self._notify(order, "rejected", {"reason": "fok_insufficient_liquidity"})
                return []

        trades = self._match(order)

        if order._quantity == 0:
            order.status = OrderStatus.FILLED
            return trades

        # something is left unmatched
        if order.order_type == OrderType.GTC:
            order.status = OrderStatus.PARTIALLY_FILLED if trades else OrderStatus.NEW
            book = self._get_book(order._stock)
            tree = book[order._type]
            qnode = tree.add_order(order)
            self._resting_index[order._id] = {
                "symbol": order._stock, "side": order._type,
                "price": order._price, "qnode": qnode, "order": order,
            }
        else:  # IOC (FOK never reaches here with leftover, since it's rejected up front)
            leftover = order._quantity
            order._quantity = 0
            order.status = OrderStatus.PARTIALLY_FILLED if trades else OrderStatus.CANCELLED
            self._notify(order, "ioc_remainder_cancelled", {"cancelled_quantity": leftover})

        return trades

    def _match(self, order: Orders) -> list[dict]:
        book = self._get_book(order._stock)
        opposite_side = "sell" if order._type == "buy" else "buy"
        opposite_tree = book[opposite_side]
        best_is_min = (order._type == "buy")

        trades = []

        while order._quantity > 0:
            level = opposite_tree.peek_best(best_is_min=best_is_min)
            if level is None:
                break

            if order._type == "buy" and order._price < level.key:
                break
            if order._type == "sell" and order._price > level.key:
                break

            resting_qnode = level.queue.peek()
            if resting_qnode is None:
                opposite_tree.unload_if_empty(level.key)
                continue

            resting_order = resting_qnode._order
            fill_qty = min(order._quantity, resting_order._quantity)
            fill_price = level.key

            trade = {
                "price": fill_price,
                "quantity": fill_qty,
                "buy_order_id": order._id if order._type == "buy" else resting_order._id,
                "sell_order_id": resting_order._id if order._type == "buy" else order._id,
            }
            trades.append(trade)
            self.last_trade_price[order._stock] = fill_price

            order._quantity -= fill_qty
            resting_order._quantity -= fill_qty
            level.queue.adjust_total(-fill_qty)          # keep this level's cached total in sync
            opposite_tree.refresh_quantity(level.key)    # propagate the change up the tree

            # notify BOTH sides right now -- this fill is final, don't wait for the
            # incoming order to fully resolve before telling the resting order's owner
            resting_order.status = (OrderStatus.FILLED if resting_order._quantity == 0
                                     else OrderStatus.PARTIALLY_FILLED)
            self._notify(order, "fill", trade)
            self._notify(resting_order, "fill", trade)

            if resting_order._quantity == 0:
                level.queue.pop()
                opposite_tree.unload_if_empty(level.key)
                self._resting_index.pop(resting_order._id, None)

        return trades

    # ---- cancellation ----
    def cancel(self, order_id: int) -> bool:
        entry = self._resting_index.pop(order_id, None)
        if entry is None:
            return False   # already filled, already cancelled, or never existed
        tree = self.books[entry["symbol"]][entry["side"]]
        tree.cancel_order(entry["price"], entry["qnode"])
        order = entry["order"]
        order.status = OrderStatus.CANCELLED
        self._notify(order, "cancelled", {"remaining_quantity": order._quantity})
        return True

    def best_bid(self, symbol: str):
        book = self.books.get(symbol)
        if not book:
            return None
        return book["buy"].pop_best(best_is_min=False)   # highest buy price

    def best_ask(self, symbol: str):
        book = self.books.get(symbol)
        if not book:
            return None
        return book["sell"].pop_best(best_is_min=True)    # lowest sell price


class LinkedListNode[X]:
    """ generic linked list node """
    def __init__(self, val: X):
        self._val = val
        self._next = None

    def getVal(self):
        return self._val

    def getNext(self):
        return self._next

    def setNext(self, node: LinkedListNode[X] | None):
        self._next = node

class LinkedList[X]:
    """ generic linked list """
    def __init__(self):
        self._head: LinkedListNode[X] | None = None
        self._tail: LinkedListNode[X] | None = None
        self._length = 0

    def pop(self):
        if self._head is None:
            return None
        temp = self._head
        self._head = self._head.getNext()
        self._length -= 1
        if self._head is None:
            self._tail = None
        return temp

    def append(self, node: LinkedListNode[X]):
        if self._tail:
            self._tail.setNext(node)
            self._tail = node
        else:
            self._head = node
            self._tail = node

        self._length += 1

    def getLength(self) -> int:
        return self._length

class RequestQueueNode(LinkedListNode[Orders]):
    """ queue for requests """
    def __init__(self, val):
        super().__init__(val)

class RequestQueue(LinkedList[Orders]):
    """ queue for requests """
    def __init__(self):
        super().__init__()

    def enqueue(self, order: Orders):
        """ creates a queue and appends the order to the queue """
        self.append(RequestQueueNode(order))

    def dequeue(self) -> Orders | None:
        node = self.pop()
        return node.getVal() if node else None
