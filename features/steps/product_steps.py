from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from behave import given, then, when

from app.eshop import Order, Product, ShoppingCart
from services import ShippingService


@given('a product with name "{name}", price {price} and availability {availability}')
def step_create_product(context, name, price, availability):
    context.product = Product(name=name, price=int(price), available_amount=int(availability))


@given('an empty shopping cart')
def step_create_cart(context):
    context.cart = ShoppingCart()
    context.operation_success = None
    context.availability_result = None
    context.order = None


@when('I check product availability for amount {amount}')
def step_check_availability(context, amount):
    try:
        context.availability_result = context.product.is_available(int(amount))
    except Exception:
        context.availability_result = None


@then('availability result should be True')
def step_assert_true(context):
    assert context.availability_result is True


@then('availability result should be False')
def step_assert_false(context):
    assert context.availability_result is False


@when('I buy product in amount {amount}')
def step_buy_product(context, amount):
    context.product.buy(int(amount))


@then('product availability should become {expected}')
def step_check_availability_amount(context, expected):
    assert context.product.available_amount == int(expected)


@when('I add the product to cart in amount {amount}')
def step_add_product_to_cart(context, amount):
    try:
        context.cart.add_product(context.product, int(amount))
        context.operation_success = True
    except Exception:
        context.operation_success = False


@then('product should be in the cart')
def step_product_in_cart(context):
    assert context.cart.contains_product(context.product) is True


@then('add to cart operation should fail')
def step_add_failed(context):
    assert context.operation_success is False


@then('cart total should be {expected_total}')
def step_cart_total(context, expected_total):
    assert context.cart.calculate_total() == int(expected_total)


@when('I remove the product from the cart')
def step_remove_product(context):
    context.cart.remove_product(context.product)


@then('product should not be in the cart')
def step_product_not_in_cart(context):
    assert context.cart.contains_product(context.product) is False


@when('I create an order from the cart')
def step_create_order(context):
    shipping_service = MagicMock(spec=ShippingService)
    shipping_service.create_shipping.return_value = 'shipping-from-bdd'
    context.order = Order(context.cart, shipping_service)


@when('I place the order')
def step_place_order(context):
    context.order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=5),
    )


@then('shopping cart should become empty')
def step_cart_empty(context):
    assert len(context.cart.products) == 0


@when('I try to add None product to cart')
def step_add_none_product(context):
    try:
        context.cart.add_product(None, 1)
        context.operation_success = True
    except Exception:
        context.operation_success = False
