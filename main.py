from fastapi import FastAPI

app = FastAPI()

products = [
    {"id": 1, "name": "Keyboard", "price": 2500.0, "quantity": 10},
    {"id": 2, "name": "Mouse", "price": 800.0, "quantity": 25},
]

@app.get("/")
def home():
    return {"message": "Product Catalog API is running",
            "version": "1.0.0"}

@app.get("/products")
def show_all_products():
    return products


from pydantic import BaseModel
class ProductCreate(BaseModel):
    name: str
    price: float
    quantity: int = 0

@app.post("/products")
def add_product(product_details :ProductCreate  ):
    next_id = max([product["id"] for product in products], default=0) + 1
    name = product_details.name
    price = product_details.price
    quantity = product_details.quantity
    products.append({"id": next_id, "name": name, "price": price, "quantity": quantity})
    return {"id": next_id, "name": name, "price": price, "quantity": quantity}

