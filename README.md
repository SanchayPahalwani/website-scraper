# FastAPI Scraper Tool

This is an advanced web scraping tool built with FastAPI that allows you to scrape product information from a target website.

## Features

- Configurable rate limiting
- Job persistence and resumability
- Scalable for large datasets
- Flexible HTML parsing
- Robust logging and error handling
- Asynchronous database/file operations
- Enhanced input validation

## Prerequisites

- Run all commands in a python virtualenv.
- Make sure redis is installed and running in background.

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Edit `app/config.py` file to edit configuration:

## Usage

1. Start the server:
   ```
   python -m app.main
   ```

2. Send a POST request to `http://localhost:8000/scrape` with the following JSON body:
   ```json
   {
     "target_url": "https://dentalstall.com/shop",
     "pages_limit": 5,
     "proxy": "http://proxy.example.com:8080",
     "rate_limit": 5.0
   }
   ```

   Make sure to include the authentication token in the request headers:
   ```
   Authorization: Bearer SuperSecretStaticToken
   ```

3. By default, the JSON output will be saved in `products.json` and the scraped images will be stored in the `product_images` directory.

## API docs

`http://localhost:8000/docs`

## Extending the Tool

To add new storage or notification strategies, create new classes in the respective directories that inherit from the base classes.

## Error Handling

The tool implements robust error handling and logging. Check the console output or log files for detailed information about the scraping process and any errors encountered.

## Scalability

For large datasets, consider using the database instead of `JsonFileStorage`. You may need to implement database migrations for your specific database schema.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
