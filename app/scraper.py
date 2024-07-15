import asyncio
import os
import time
from typing import List, Optional, AsyncGenerator
import httpx
import re
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import redis
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from .models import Product, ScraperConfig
from .storage.base import StorageStrategy
from .notification.base import NotificationStrategy
from .config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)
redis_client = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=settings.redis_db)

class RateLimiter:
    def __init__(self, rate_limit: float):
        self.rate_limit = rate_limit
        self.last_request_time = 0
    
    async def wait(self):
        current_time = time.time()
        time_since_last_req = current_time - self.last_request_time
        if time_since_last_req < self.rate_limit:
            await asyncio.sleep(self.rate_limit - time_since_last_req)
        self.last_request_time = time.time()


class Scraper:
    def __init__(
        self,
        target_url: str,
        storage: StorageStrategy,
        notification: NotificationStrategy,
        pages_limit: Optional[int] = None,
        proxy: Optional[str] = None,
        rate_limit: float = 1.0,
    ):
        self.target_url = target_url
        self.pages_limit = pages_limit
        self.proxy = proxy
        self.storage = storage
        self.notification = notification
        self.rate_limit = RateLimiter(rate_limit)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_page(self, url: str) -> str:
        await self.rate_limit.wait()
        async with httpx.AsyncClient(proxies=self.proxy) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response

    async def get_cached_product(self, product_id):
        cached_data = redis_client.get(product_id)
        if cached_data:
            return json.loads(cached_data)
        return None


    async def update_product_cache(self, product_id, product_data):
        redis_client.set(product_id, json.dumps(product_data))

    async def download_image(self, url, folder):
        if not os.path.exists(folder):
            os.makedirs(folder)

        filename = url.split('/')[-1]
        filepath = os.path.join(folder, filename)

        response = await self.fetch_page(url)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return filepath
        return None
    
    async def parse_price(self, price_str):
        # Remove currency symbol, commas, and whitespace
        clean_price = re.sub(r'[^\d.]', '', price_str)
        try:
            return float(clean_price)
        except ValueError:
            return None


    async def scrape_page(self, page: int) -> List[Product]:
        if page == 1:
            url = f"{self.target_url}"
        else:
            url = f"{self.target_url}/page/{page}"
        html = await self.fetch_page(url)
        soup = BeautifulSoup(html.content, 'html.parser')
        products = soup.find_all('li', class_='product')

        products_data = []
        for product in products:
            try:
                product_id_elem = product.find(attrs={"data-product_id": True})
                if not product_id_elem:
                    logger.info("Skipping product without ID")
                    continue
                
                product_id = product_id_elem['data-product_id']
                
                # Extract product title
                title = product.find('h2', class_='woo-loop-product__title').text.strip()
                
                # Extract product price
                price_elem = product.find('span', class_='price')
                if price_elem:
                    # Find the first occurrence of a price (could be sale price or regular price)
                    price_text = price_elem.find('span', class_='woocommerce-Price-amount').text.strip()
                    price = await self.parse_price(price_text)
                else:
                    price = None
                
                # Check cache
                cached_product = await self.get_cached_product(product_id)

                if cached_product:
                    image_path = cached_product['image_path']
                    if cached_product['price'] == price:
                        logger.info(f"No price change for product {product_id}. Using cached data.")
                        title = cached_product['title']
                    else:
                        logger.info(f"Price changed for product {product_id}. Updating cache.")
                        await self.update_product_cache(product_id, {
                            'title': title,
                            'price': price,
                            'image_path': image_path
                        })
                else:
                    logger.info(f"New product {product_id}. Adding to cache.")
                    # Extract image path
                    img_elem = product.find('img')
                    img_url = img_elem['data-lazy-src'] if img_elem and 'data-lazy-src' in img_elem.attrs else 'Image not available'

                    # Download and save image
                    if img_url:
                        image_path = await self.download_image(img_url, 'product_images')
                    else:
                        image_path = 'Image not available'
                    # Update cache
                    await self.update_product_cache(product_id, {
                        'title': title,
                        'price': price,
                        'image_path': image_path
                    })

                product = Product(product_id=product_id, product_title=title, product_price=price, path_to_image=image_path)
                products_data.append(product)
            except Exception as e:
                logger.error(f"Error parsing product: {str(e)}")
        
        return products_data
    
    async def scrape(self) -> AsyncGenerator[Product, None]:
        logger.info("Starting scraping job")
        page = 1
        while True:
            if self.pages_limit and page > self.pages_limit:
                break
            try:
                products = await self.scrape_page(page)
                if not products:
                    break
                for product in products:
                    yield product
                logger.info(f"Scraped page {page}")
                page += 1
            except Exception as e:
                logger.error(f"Error scraping page {page}: {str(e)}")
                await self.notification.notify(f"Error scraping page {page}: {str(e)}")
                break

    logger.info("Scraping job completed")

    def save_state(self, filename: str = "scraper_state.pkl"):
        with open(filename, "wb") as f:
            pickle.dump(self.__dict__, f)

    @classmethod
    def load_state(cls, filename: str = "scraper_state.pkl"):
        with open(filename, "rb") as f:
            return cls(**pickle.load(f))
