from abc import ABC, abstractmethod
from typing import List
from ..models import Product

class StorageStrategy(ABC):
    @abstractmethod
    async def save(self, products: List[Product]):
        pass
