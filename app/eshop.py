from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import uuid
from services import ShippingService


class Product:
    def __init__(self, name, price, available_amount):
        self.name = name
        self.price = price
        self.available_amount = available_amount

    def is_available(self, requested_amount):
        return requested_amount >= 0 and self.available_amount >= requested_amount

    def buy(self, requested_amount):
        if not self.is_available(requested_amount):
            raise ValueError(
                f"Product {self.name} has only {self.available_amount} items"
            )
        self.available_amount -= requested_amount

    def __eq__(self, other):
        if not isinstance(other, Product):
            return NotImplemented
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name


class ShoppingCart:
    def __init__(self):
        self.products = {}

    def contains_product(self, product):
        return product in self.products

    def calculate_total(self):
        return sum(product.price * count for product, count in self.products.items())

    def add_product(self, product: Product, amount: int):
        if product is None:
            raise ValueError("Product cannot be None")
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")

        current_amount = self.products.get(product, 0)
        total_amount = current_amount + amount

        if not product.is_available(total_amount):
            raise ValueError(
                f"Product {product} has only {product.available_amount} items"
            )

        self.products[product] = total_amount

    def remove_product(self, product):
        if product in self.products:
            del self.products[product]

    def submit_cart_order(self):
        product_ids = []
        for product, count in self.products.items():
            product.buy(count)
            product_ids.append(str(product))
        self.products.clear()
        return product_ids


@dataclass
class Order:
    cart: ShoppingCart
    shipping_service: ShippingService
    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def place_order(self, shipping_type, due_date: datetime = None):
        if due_date is None:
            due_date = datetime.now(timezone.utc) + timedelta(seconds=3)

        product_ids = self.cart.submit_cart_order()
        return self.shipping_service.create_shipping(
            shipping_type,
            product_ids,
            self.order_id,
            due_date,
        )


@dataclass
class Shipment:
    shipping_id: str
    shipping_service: ShippingService

    def check_shipping_status(self):
        return self.shipping_service.check_status(self.shipping_id)
