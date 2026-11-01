import json

from fastapi.testclient import TestClient
import pytest
import  main

client = TestClient(main.app)

@pytest.fixture(autouse=True)
def reset_products():
    main.products.clear()
    yield
    main.products.clear()

def test_home_returns_successful_response():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Product Catalog API is running",
        "version": "1.0.0",
    }

def test_create_product():
    product_data = {
        "name": "Keyboard",
        "price": 49.99,
        "quantity": 5
    }

    response = client.post("/products", json = product_data)
    assert  response.status_code == 201
    assert  response.json()["name"] == "Keyboard"
    assert  response.json()["price"] == 49.99
    assert  response.json()["quantity"] == 5

def test_create_product_with_zero_price():
    product_data = {
        "name": "Keyboard",
        "price": 0,
        "quantity": 5
    }

    response = client.post("/products", json = product_data)
    assert response.status_code == 422


def test_get_nonexistent_product():
    response = client.get("/products/999")
    assert response.status_code == 404

def test_create_product_with_blank_name():
    product_data = {
        "name": "   ",
        "price": 49.99,
        "quantity": 5
    }

    response = client.post("/products", json=product_data)

    assert response.status_code == 422

def test_create_product_with_small_positive_price():
    product_data = {
        "name": "Small Item",
        "price": 0.01,
        "quantity": 1
    }

    response = client.post("/products", json=product_data)

    assert response.status_code == 201

def test_create_product_with_negative_quantity():
    product_data = {
        "name": "Keyboard",
        "price": 49.99,
        "quantity": -1
    }

    response = client.post("/products", json=product_data)

    assert response.status_code == 422


def test_create_product_with_zero_quantity():
    product_data = {
        "name": "Keyboard",
        "price": 49.99,
        "quantity": 0
    }

    response = client.post("/products", json=product_data)

    assert response.status_code == 201
    assert response.json()["quantity"] == 0

def test_get_product():
    product_data = {
        "name": "Keyboard",
        "price": 49.99,
        "quantity": 5
    }
    # create product
    create_product = client.post("/products", json=product_data)
    return_data = create_product.json()
    assert create_product.status_code == 201

    # get all product
    response = client.get("/products")
    products = response.json()
    for product in products:
        if product["id"] == return_data["id"]:
            assert response.status_code ==200
            assert product["name"] == "Keyboard"
            assert  product["price"] == 49.99
            assert product["quantity"] == 5
            assert product["id"] == return_data["id"]
            break
    else:
         pytest.fail("Created product was not found in GET /products response")
