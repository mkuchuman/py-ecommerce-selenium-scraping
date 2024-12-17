import csv
from dataclasses import dataclass, astuple, fields
from typing import Any
from urllib.parse import urljoin
from bs4 import Tag, BeautifulSoup
from selenium import webdriver
from selenium.common import (
    NoSuchElementException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://webscraper.io/"
URLS = [
    ("home",
     urljoin(BASE_URL, "test-sites/e-commerce/more")),
    ("computers",
     urljoin(BASE_URL, "test-sites/e-commerce/more/computers")),
    ("laptops",
     urljoin(BASE_URL, "test-sites/e-commerce/more/computers/laptops")),
    ("tablets",
     urljoin(BASE_URL, "test-sites/e-commerce/more/computers/tablets")),
    ("phones",
     urljoin(BASE_URL, "test-sites/e-commerce/more/phones")),
    ("touch",
     urljoin(BASE_URL, "test-sites/e-commerce/more/phones/touch")),
]


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def normalize_text(text: str) -> str:
    return text.replace("\xa0", " ").strip() if text else ""


def write_products_to_csv(products: list, output_csv_path: str) -> None:
    with open(output_csv_path + ".csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_soup(page_source: str) -> BeautifulSoup:
    return BeautifulSoup(page_source, "html.parser")


def safe_get(element: Tag,
             selector: str,
             attr: str = None,
             default: Any = None
             ) -> str:
    try:
        selected = element.select_one(selector)
        if not selected:
            return default
        return normalize_text(
            selected[attr]
        ) if attr else normalize_text(selected.text)
    except (AttributeError, TypeError):
        return default


def get_product(product: Tag) -> Product:
    return Product(
        title=safe_get(product,
                       "a.title", "title", "No Title"),
        description=safe_get(product,
                             "p.description", default="No Description"),
        price=float(safe_get(product,
                             "h4.price", default="0").replace("$", "")),
        rating=(
            len(product.select("span.ws-icon-star"))
            if product.select("span.ws-icon-star")
            else 0
        ),
        num_of_reviews=int(safe_get(product,
                                    "p.review-count", default="0").split()[0]),
    )


def parse_single_page(page: BeautifulSoup) -> list[Product]:
    products = (
        page.select("div.product-wrapper.card-body")
        if page.select("div.product-wrapper.card-body")
        else []
    )
    return [get_product(product) for product in products if product]


def check_for_cookies(driver: webdriver) -> None:
    try:
        cookies = driver.find_element(By.CLASS_NAME, "acceptCookies")
        cookies.click()
    except NoSuchElementException:
        pass


def load_more_products(driver: webdriver) -> None:
    while True:
        try:
            button = driver.find_element(By.CLASS_NAME,
                                         "ecomerce-items-scroll-more")
            button.click()
        except (
            NoSuchElementException,
            ElementNotInteractableException,
            ElementClickInterceptedException,
        ):
            break


def get_all_products() -> None:
    service = Service(ChromeDriverManager().install())
    with webdriver.Chrome(service=service) as driver:
        for name, url in URLS:
            driver.get(url)
            check_for_cookies(driver)
            load_more_products(driver)
            current_page = get_soup(driver.page_source)
            parsed_products = parse_single_page(current_page)
            write_products_to_csv(parsed_products, name)


if __name__ == "__main__":
    get_all_products()
