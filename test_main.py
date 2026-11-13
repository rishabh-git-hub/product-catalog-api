import json

from fastapi.testclient import TestClient
import pytest
import  main
from unittest.mock import patch, Mock


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
    product_data = [
    {
        "name": "mouse",
        "price": 40,
        "quantity": 2
    },
    {
        "name": "Keyboard",
        "price": 49.99,
        "quantity": 5
    }
    ]
    # create  all product
    return_data = []
    for product in product_data:
        create_product = client.post("/products", json=product)
        assert create_product.status_code == 201
        return_data.append(create_product.json())

    return_data_id = None
    for data in return_data:
        if data["name"] == "Keyboard":
            return_data_id = data["id"]

    if return_data_id is None:
        pytest.fail("Keyboard was not created")

    # get all product and verify for product "keyboard"
    response = client.get("/products")
    assert response.status_code == 200
    products = response.json()
    for product in products:
        if product["id"] == return_data_id:
                assert product["name"] == "Keyboard"
                assert  product["price"] == 49.99
                assert product["quantity"] == 5
                break
    else:
         pytest.fail("Created product was not found in GET /products response")


def test_enrich_product_validation_error():
    prompt = {}

    response = client.post("/products/enrich", json=prompt)
    assert response.status_code == 422
 

# 2. We put the @patch "sticker" on top of our test function.
# We tell it the exact path to the tool we want to fake: "main.requests.post".
# (This assumes your FastAPI code is inside a file named main.py)
@patch("main.requests.post")
def test_enrich_product_timeout(mock_post):
    mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")
    payload = {"prompt": "keyboard"}
    response = client.post("/products/enrich",json=payload)
    # 3. Inside the function, we can now configure our stunt double
    assert response.status_code == 504


@patch("main.requests.post")
def test_enrich_product_provider_error(mock_post):
    mock_post.side_effect = requests.exceptions.RequestException("server Unavailable")
    payload = {"prompt": "keyboard"}
    response = client.post("/products/enrich",json=payload)
    # 3. Inside the function, we can now configure our stunt double
    assert response.status_code == 503


