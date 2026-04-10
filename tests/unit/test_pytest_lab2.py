from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from app.eshop import Product, ShoppingCart, Order
from services import ShippingService


def build_order(cart):
    shipping_service = MagicMock(spec=ShippingService)
    shipping_service.create_shipping.return_value = "shipping-123"
    return Order(cart, shipping_service), shipping_service


def test_product_is_available_exact_amount():
    product = Product(name="Phone", price=1000, available_amount=5)
    assert product.is_available(5) is True


def test_product_is_not_available_greater_amount():
    product = Product(name="Phone", price=1000, available_amount=5)
    assert product.is_available(6) is False


def test_product_is_available_for_zero_amount():
    product = Product(name="Phone", price=1000, available_amount=5)
    assert product.is_available(0) is True


def test_buy_product_decreases_available_amount():
    product = Product(name="Phone", price=1000, available_amount=5)
    product.buy(2)
    assert product.available_amount == 3


def test_add_available_product_to_cart():
    product = Product(name="Phone", price=1000, available_amount=5)
    cart = ShoppingCart()
    cart.add_product(product, 2)
    assert cart.contains_product(product) is True


def test_add_unavailable_product_to_cart():
    product = Product(name="Phone", price=1000, available_amount=5)
    cart = ShoppingCart()
    with pytest.raises(ValueError):
        cart.add_product(product, 10)


def test_cart_total_calculated_correctly():
    product = Product(name="Phone", price=1000, available_amount=5)
    cart = ShoppingCart()
    cart.add_product(product, 3)
    assert cart.calculate_total() == 3000


def test_remove_product_from_cart():
    product = Product(name="Phone", price=1000, available_amount=5)
    cart = ShoppingCart()
    cart.add_product(product, 2)
    cart.remove_product(product)
    assert cart.contains_product(product) is False


def test_place_order_clears_shopping_cart():
    product = Product(name="Phone", price=1000, available_amount=5)
    cart = ShoppingCart()
    cart.add_product(product, 2)
    order, shipping_service = build_order(cart)
    result = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    assert result == "shipping-123"
    assert len(cart.products) == 0
    shipping_service.create_shipping.assert_called_once()


def test_add_none_product_to_cart():
    cart = ShoppingCart()
    with pytest.raises(ValueError):
        cart.add_product(None, 1)
