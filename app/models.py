from typing import Optional
from pydantic import BaseModel, HttpUrl, PositiveInt, PositiveFloat

class ScraperConfig(BaseModel):
    target_url: HttpUrl
    pages_limit: Optional[PositiveInt] = None
    proxy: Optional[str] = None
    rate_limit: PositiveFloat = 1.0

class Product(BaseModel):
    product_id: str
    product_title: str
    product_price: float
    path_to_image: str
