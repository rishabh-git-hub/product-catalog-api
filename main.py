# uv run uvicorn main:app --reload

import os
from dotenv import load_dotenv
from fastapi import FastAPI , HTTPException
from pydantic import BaseModel, Field , field_validator
from typing import Optional
import requests 
import json


load_dotenv()

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

class ProductEnrichmentRequest(BaseModel):
    prompt : str

class ProductEnrichmentResponse(BaseModel):
    name : str
    price : float
    description: str         

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


@app.post("/products/enrich", status_code=201)
def enrich_product(request_data: ProductEnrichmentRequest) -> ProductEnrichmentResponse:
    prompt = f"Generate a creative product name, a short marketing description, and a realistic price in rupees for this item: {request_data.prompt}. Return ONLY valid JSON with keys 'name', 'price', and 'description'."
    
    url = "https://api.euron.one/api/v1/euri/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ.get('EURON_API_KEY')}"
    }
    payload = {
        "model": "gpt-5.3-chat-latest",
        "messages": [{"role": "user", "content": prompt}],
        # Some providers support structured output natively, but if not, 
        # we can explicitly ask for JSON in the prompt as done above.
        "response_format": {"type": "json_object"} 
    }

    try:
        # Make the HTTP POST request to Euron
        response = requests.post(url, headers=headers, json=payload , timeout=5)
        
        # Raise an exception if the HTTP status code is an error (4xx, 5xx)
        response.raise_for_status()
        
        # Parse the JSON response from Euron
        response_data = response.json()
        
        # Extract the actual text content from the Euron response structure
        # (This structure depends on the specific provider's API format)
        content_string = response_data["choices"][0]["message"]["content"]
        
        # Parse that content string into a Python dictionary
        content_dict = json.loads(content_string)
        
        # Validate the dictionary using our Pydantic model
        validated_response = ProductEnrichmentResponse(**content_dict)
        return validated_response

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Provider timeout Error")     

    except requests.exceptions.RequestException as e:
        # Catch any network or HTTP errors from the Euron API call
        print(f"Provider Error: {e}") # Print the raw error to your Uvicorn terminal for debugging
        raise HTTPException(
            status_code=503, 
            detail="The AI provider is currently experiencing issues. Please try again later."
        )
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        # Catch parsing errors if the AI returns bad JSON or misses a key
        print(f"Parsing Error: {e}") 
        raise HTTPException(
            status_code=500,
            detail="Failed to process the response from the AI provider."
        )