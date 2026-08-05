"""
Order book implementation.

Design:
- Each price level is a node in an AVL tree (self-balancing BST), keyed by price.
- Each price-level node holds a FIFO queue (doubly linked list) of orders at that price,
  giving price-time priority.
- When a price level's queue empties, the node is deleted ("unloaded") from the tree.
- A top-level dict maps stock symbol -> {"buy": OrderTree, "sell": OrderTree}.
"""

from datetime import datetime


class Orders:
    """Details about a single order."""

    def __init__(self, id: int, user_id: int, type: str, price: float, stock: str, quantity: int):
        self._id = id
        self._user_id = user_id
        self._stock = stock
        self._type = type          # "buy" / "sell"
        self._price = price
        self._quantity = quantity
        self.time = datetime.now()

    def __repr__(self):
        return f"Order(id={self._id}, {self._type} {self._quantity}@{self._price})"


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

    def is_empty(self) -> bool:
        return self._head is None          # bug fix: was self.head (wrong attr)

    def __len__(self):
        return self._size

    def pop(self) -> "OrderQueueNode | None":
        """Pop the oldest order (FIFO) off the front of the queue."""
        if not self._head:
            return None

        x = self._head
        self._head = self._head._next

        if self._head:                     # bug fix: was `if x._head` (attr didn't exist)
            self._head._prev = None
        else:
            self._tail = None              # bug fix: tail wasn't reset when queue drains

        x._next = None
        x._prev = None
        self._size -= 1
        return x

    def append(self, node: OrderQueueNode) -> None:
        if not self._head:
            self._head = node
            self._tail = node
            self._size += 1
            return                          # bug fix: previously fell through and
                                             # crashed on self._tail.setNext(...) (tail was None)

        self._tail.setNext(node)
        node.setPrev(self._tail)
        self._tail = node
        self._size += 1


class TreeNode:
    """A price level in the AVL tree. Holds the queue of orders resting at that price."""

    def __init__(self, key: float, queue: OrderQueue):
        self.key = key                      # price
        self.queue = queue                  # OrderQueue of OrderQueueNode at this price
        self.left: "TreeNode | None" = None
        self.right: "TreeNode | None" = None
        self.height = 1


class OrderTree:
    """Self-balancing AVL tree of price levels (one side of the book: all buys or all sells)."""

    def __init__(self):
        self.root: "TreeNode | None" = None

    # ---- height / balance helpers ----
    def get_height(self, node: "TreeNode | None") -> int:
        return node.height if node else 0

    def get_balance(self, node: "TreeNode | None") -> int:
        return self.get_height(node.left) - self.get_height(node.right) if node else 0

    def _rotate_right(self, z: TreeNode) -> TreeNode:
        y = z.left
        T2 = y.right
        y.right = z
        z.left = T2
        z.height = 1 + max(self.get_height(z.left), self.get_height(z.right))
        y.height = 1 + max(self.get_height(y.left), self.get_height(y.right))
        return y

    def _rotate_left(self, z: TreeNode) -> TreeNode:
        y = z.right
        T2 = y.left
        y.left = z
        z.right = T2
        z.height = 1 + max(self.get_height(z.left), self.get_height(z.right))
        y.height = 1 + max(self.get_height(y.left), self.get_height(y.right))
        return y

    def _rebalance(self, node: TreeNode, key: float) -> TreeNode:
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

    # ---- find (get the queue at a price, without modifying the tree) ----
    def find(self, price: float) -> "TreeNode | None":
        node = self.root
        while node:
            if price == node.key:
                return node
            node = node.left if price < node.key else node.right
        return None

    # ---- insert an order at its price level, creating the level if needed ----
    def add_order(self, order: Orders) -> OrderQueueNode:
        qnode = OrderQueueNode(order)
        existing = self.find(order._price)
        if existing:
            existing.queue.append(qnode)
        else:
            self.root = self._insert(self.root, order._price, qnode)
        return qnode

    def _insert(self, root: "TreeNode | None", key: float, qnode: OrderQueueNode) -> TreeNode:
        if not root:
            new_node = TreeNode(key, OrderQueue())
            new_node.queue.append(qnode)
            return new_node

        if key < root.key:
            root.left = self._insert(root.left, key, qnode)
        elif key > root.key:
            root.right = self._insert(root.right, key, qnode)
        else:
            root.queue.append(qnode)
            return root

        root.height = 1 + max(self.get_height(root.left), self.get_height(root.right))
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
                return root.right
            if root.right is None:
                return root.left
            successor = self._find_extreme(root.right, go_left=True)
            root.key = successor.key
            root.queue = successor.queue
            root.right = self._delete(root.right, successor.key)

        root.height = 1 + max(self.get_height(root.left), self.get_height(root.right))
        return self._rebalance(root, key)

    def inorder(self, root: "TreeNode | None" = "__self__") -> list[float]:
        if root == "__self__":
            root = self.root
        if not root:
            return []
        return self.inorder(root.left) + [root.key] + self.inorder(root.right)


class OrderBookManager:
    """Top-level registry: stock symbol -> {"buy": OrderTree, "sell": OrderTree}."""

    def __init__(self):
        self.books: dict[str, dict[str, OrderTree]] = {}

    def _get_book(self, symbol: str) -> dict[str, OrderTree]:
        if symbol not in self.books:
            self.books[symbol] = {"buy": OrderTree(), "sell": OrderTree()}
        return self.books[symbol]

    def submit(self, order: Orders) -> OrderQueueNode:
        book = self._get_book(order._stock)
        tree = book[order._type]           # "buy" or "sell"
        return tree.add_order(order)

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