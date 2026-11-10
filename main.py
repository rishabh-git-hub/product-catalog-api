# uv run uvicorn main:app --reload
from fastapi import FastAPI , HTTPException
from pydantic import BaseModel, Field , field_validator
from typing import Optional

app = FastAPI()

products = [
    {"id": 1, "name": "Keyboard", "price": 2500.0, "quantity": 10},
    {"id": 2, "name": "Mouse", "price": 800.0, "quantity": 25},
]


class ProductCreate(BaseModel):
    name: str 
    price: float = Field(gt=0)
    quantity: int = Field(default=0, ge=0) 

    @field_validator("name")
    @classmethod
    def validate_name(cls, name):
        return clean_name(name)


class ProductUpdate(BaseModel):
    name: str | None = None
    price: float | None = Field(default=None, gt=0)
    quantity: int | None = Field(default=None, ge=0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, name):
        if name is None:
            return name
        return clean_name(name)      

def clean_name(name):
    cleaned_name = name.strip()
    if cleaned_name == "":
        raise ValueError("Name cannot be empty")
    return cleaned_name


@app.get("/")
def home():
    return {"message": "Product Catalog API is running",
            "version": "1.0.0"}

@app.get("/products")
def show_all_products():
    return products


@app.post("/products",status_code=201)
def add_product(product_details :ProductCreate):
    next_id = max([product["id"] for product in products], default=0) + 1
    name = product_details.name
    price = product_details.price
    quantity = product_details.quantity
    products.append({"id": next_id, "name": name, "price": price, "quantity": quantity})
    return {"id": next_id, "name": name, "price": price, "quantity": quantity}

@app.get("/products/{product_id}")
def get_product(product_id:int):
    for product in products:
        if product["id"] == product_id:
            return product

    raise HTTPException(status_code=404, detail="Product not found")


@app.put("/products/{product_id}")
def  update_product(product_id:int, product_details:ProductCreate):
    for product in products:
        if product["id"] == product_id:
            product["name"] =product_details.name
            product["quantity"] = product_details.quantity
            product["price"] = product_details.price
            return product

    raise HTTPException(status_code=404, detail= "Product not found")


@app.delete("/products/{product_id}")
def delete_product(product_id:int):
    for product in products:
        if product["id"] == product_id:
            products.remove(product)
            return product
    raise HTTPException (status_code= 404, detail="Product not found")


@app.patch("/products/{product_id}")
def update_product_partial(product_id:int, product_details:ProductUpdate):
    for product in products:
        if product["id"] == product_id:
            # 1. Get a dictionary of only the fields the client sent
            update_data = product_details.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                product[key] = value     
            return product
    raise HTTPException(status_code=404, detail="Product not found")        
