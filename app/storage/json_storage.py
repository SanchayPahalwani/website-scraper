import json
from typing import List
from .base import StorageStrategy
from ..models import Product

class JsonFileStorage(StorageStrategy):
    def __init__(self, filename: str = "products.json"):
        self.filename = filename
    
    async def save(self, products: List[Product]):
        try:
            # Read existing products
            with open(self.filename, "r") as f:
                existing_products = json.load(f)
        except Exception:
            existing_products = []

        # Convert existing products to a dictionary for easy lookup
        existing_product_dict = {product['product_id']: product for product in existing_products}

        # Update existing products or add new ones
        for new_product in products:
            if new_product.product_id in existing_product_dict:
                # Update existing product
                existing_product_dict[new_product.product_id] = new_product.dict()
            else:
                # Add new product
                existing_product_dict[new_product.product_id] = new_product.dict()
        
        # Convert back to list
        updated_products = list(existing_product_dict.values())

        # Save updated products
        with open(self.filename, "w") as f:
            json.dump(updated_products, f, indent=2)
