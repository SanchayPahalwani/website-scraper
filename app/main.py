import logging
from fastapi import FastAPI, Depends, HTTPException
from .models import ScraperConfig
from .scraper import Scraper
from .auth import verify_token
from .storage.json_storage import JsonFileStorage
from .notification.console_notification import ConsoleNotification
from .config import get_settings

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.post("/scrape")
async def start_scraping(config: ScraperConfig, token: str = Depends(verify_token)):
    settings = get_settings()
    storage = JsonFileStorage(filename=settings.json_storage_file)
    notification = ConsoleNotification()

    scraper = Scraper(
        target_url=str(config.target_url),
        pages_limit=config.pages_limit,
        proxy=config.proxy,
        rate_limit=config.rate_limit,
        storage=storage,
        notification=notification,
    ) 
    try:
        products = [product async for product in scraper.scrape()]
        await storage.save(products)
        await notification.notify(f"Scraped and saved {len(products)} products")
        # await scraper.scrape()
        return {"message": "Scraping completed successfully"}
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Scraping failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
