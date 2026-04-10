import uuid
import random
import time
from datetime import datetime, timedelta, timezone

import boto3
import pytest

from app.eshop import Product, ShoppingCart, Order, Shipment
from services import ShippingService
from services.repository import ShippingRepository
from services.publisher import ShippingPublisher
from services.config import (
    AWS_ENDPOINT_URL,
    AWS_REGION,
    SHIPPING_QUEUE,
    SHIPPING_TABLE_NAME,
)


def build_shipping_service():
    return ShippingService(ShippingRepository(), ShippingPublisher())


def build_cart(product_name="Product", amount=2, available_amount=10):
    cart = ShoppingCart()
    cart.add_product(
        Product(
            name=product_name,
            price=random.random() * 1000,
            available_amount=available_amount,
        ),
        amount=amount,
    )
    return cart


def get_sqs_client():
    return boto3.client(
        "sqs",
        endpoint_url=AWS_ENDPOINT_URL,
        region_name=AWS_REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )


def get_dynamo_table():
    dynamo = boto3.resource(
        "dynamodb",
        endpoint_url=AWS_ENDPOINT_URL,
        region_name=AWS_REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    return dynamo.Table(SHIPPING_TABLE_NAME)


@pytest.fixture
def clean_queue():
    sqs_client = get_sqs_client()
    queue_url = sqs_client.get_queue_url(QueueName=SHIPPING_QUEUE)["QueueUrl"]

    while True:
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=1,
        )
        messages = response.get("Messages", [])
        if not messages:
            break

        for msg in messages:
            sqs_client.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=msg["ReceiptHandle"],
            )

    return queue_url


def test_place_order_creates_shipping_record_in_dynamodb(dynamo_resource, clean_queue):
    shipping_service = build_shipping_service()
    cart = build_cart(product_name="Product-A", amount=3)

    order = Order(cart, shipping_service)
    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=5),
    )

    item = ShippingRepository().get_shipping(shipping_id)

    assert item is not None
    assert item["shipping_id"] == shipping_id
    assert item["order_id"] == order.order_id
    assert item["product_ids"] == "Product-A"


def test_place_order_sets_status_in_progress(dynamo_resource, clean_queue):
    shipping_service = build_shipping_service()
    cart = build_cart(product_name="Product-B", amount=2)

    order = Order(cart, shipping_service)
    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[1],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=5),
    )

    status = shipping_service.check_status(shipping_id)

    assert status == ShippingService.SHIPPING_IN_PROGRESS


def test_place_order_clears_cart_after_submit(dynamo_resource, clean_queue):
    shipping_service = build_shipping_service()
    cart = build_cart(product_name="Product-C", amount=2)

    order = Order(cart, shipping_service)
    order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=5),
    )

    assert cart.products == {}


def test_place_order_reduces_product_available_amount(dynamo_resource, clean_queue):
    shipping_service = build_shipping_service()
    product = Product(name="Product-D", price=100, available_amount=10)
    cart = ShoppingCart()
    cart.add_product(product, 4)

    order = Order(cart, shipping_service)
    order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=5),
    )

    assert product.available_amount == 6


def test_check_status_via_shipment_object(dynamo_resource, clean_queue):
    shipping_service = build_shipping_service()
    cart = build_cart(product_name="Product-E", amount=1)

    order = Order(cart, shipping_service)
    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[2],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=5),
    )

    shipment = Shipment(shipping_id, shipping_service)

    assert shipment.check_shipping_status() == ShippingService.SHIPPING_IN_PROGRESS


def test_process_shipping_completes_shipping_with_future_due_date(dynamo_resource, clean_queue):
    shipping_service = build_shipping_service()
    cart = build_cart(product_name="Product-F", amount=1)

    order = Order(cart, shipping_service)
    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=5),
    )

    shipping_service.process_shipping(shipping_id)

    assert shipping_service.check_status(shipping_id) == ShippingService.SHIPPING_COMPLETED


def test_process_shipping_batch_completes_shipping_from_queue(dynamo_resource, clean_queue):
    shipping_service = build_shipping_service()
    cart = build_cart(product_name="Product-G", amount=2)

    order = Order(cart, shipping_service)
    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=5),
    )

    shipping_service.process_shipping_batch()

    assert shipping_service.check_status(shipping_id) == ShippingService.SHIPPING_COMPLETED


def test_fail_shipping_changes_status_to_failed(dynamo_resource, clean_queue):
    shipping_service = build_shipping_service()
    repository = ShippingRepository()

    shipping_id = repository.create_shipping(
        shipping_type=ShippingService.list_available_shipping_type()[0],
        product_ids=["Product-H"],
        order_id=str(uuid.uuid4()),
        status=ShippingService.SHIPPING_CREATED,
        due_date=datetime.now(timezone.utc) + timedelta(minutes=5),
    )

    shipping_service.fail_shipping(shipping_id)

    assert shipping_service.check_status(shipping_id) == ShippingService.SHIPPING_FAILED


def test_complete_shipping_changes_status_to_completed(dynamo_resource, clean_queue):
    shipping_service = build_shipping_service()
    repository = ShippingRepository()

    shipping_id = repository.create_shipping(
        shipping_type=ShippingService.list_available_shipping_type()[0],
        product_ids=["Product-I"],
        order_id=str(uuid.uuid4()),
        status=ShippingService.SHIPPING_CREATED,
        due_date=datetime.now(timezone.utc) + timedelta(minutes=5),
    )

    shipping_service.complete_shipping(shipping_id)

    assert shipping_service.check_status(shipping_id) == ShippingService.SHIPPING_COMPLETED


def test_two_orders_create_two_shipping_records(dynamo_resource, clean_queue):
    shipping_service = build_shipping_service()

    cart1 = build_cart(product_name="Product-J1", amount=1)
    cart2 = build_cart(product_name="Product-J2", amount=1)

    order1 = Order(cart1, shipping_service)
    order2 = Order(cart2, shipping_service)

    shipping_id_1 = order1.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    shipping_id_2 = order2.place_order(
        ShippingService.list_available_shipping_type()[1],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=5),
    )

    item1 = ShippingRepository().get_shipping(shipping_id_1)
    item2 = ShippingRepository().get_shipping(shipping_id_2)

    assert shipping_id_1 != shipping_id_2
    assert item1 is not None
    assert item2 is not None
    assert item1["order_id"] != item2["order_id"]