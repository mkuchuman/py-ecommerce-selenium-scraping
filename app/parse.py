import csv
from dataclasses import dataclass, astuple, fields
from urllib.parse import urljoin
from bs4 import Tag, BeautifulSoup
from selenium import webdriver
from selenium.common import (
    ElementNotInteractableException,
    ElementClickInterceptedException,
)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By

BASE_URL = "https://webscraper.io/"
urls = (
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
)

_driver: WebDriver | None = None


def set_driver(driver: WebDriver) -> None:
    global _driver
    _driver = driver


def get_driver() -> WebDriver:
    return _driver


@dataclass
class Product:
    title: str
    description: str
    price: float
    rating: int
    num_of_reviews: int


PRODUCT_FIELDS = [field.name for field in fields(Product)]


def normalize_text(text: str) -> str:
    return text.replace("\xa0", " ").strip()


def write_products_to_csv(products: list, output_csv_path: str) -> None:
    with open(output_csv_path + ".csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(PRODUCT_FIELDS)
        writer.writerows([astuple(product) for product in products])


def get_soup(page_source: str) -> BeautifulSoup:
    return BeautifulSoup(page_source, "html.parser")


def get_product(product: Tag) -> Product:
    return Product(
        title=normalize_text(
            product.select_one("a.title")["title"]),
        description=normalize_text(
            product.select_one("p.description").text),
        price=float(
            product.select_one("h4.price").text.replace("$", "")),
        rating=len(
            product.select("span.ws-icon-star")),
        num_of_reviews=int(
            product.select_one("p.review-count").text.split()[0]),
    )


def parse_single_page(page: BeautifulSoup) -> list[Product]:
    products = page.select("div.product-wrapper.card-body")
    return [get_product(product) for product in products]


def check_for_cookies(driver: WebDriver) -> None:
    if get_soup(driver.page_source).select_one(".acceptCookies"):
        cookies = driver.find_element(By.CLASS_NAME, "acceptCookies")
        cookies.click()


def get_all_products() -> None:
    with webdriver.Chrome() as driver:
        set_driver(driver)
        for name, url in urls:
            driver = get_driver()
            driver.get(url)
            check_for_cookies(driver)
            current_page = get_soup(driver.page_source)
            while current_page.select_one("a.ecomerce-items-scroll-more"):
                button = driver.find_element(
                    By.CLASS_NAME, "ecomerce-items-scroll-more"
                )
                try:
                    button.click()
                except (
                    ElementNotInteractableException,
                    ElementClickInterceptedException,
                ):
                    break
            current_page = get_soup(driver.page_source)
            parse_result = parse_single_page(current_page)
            write_products_to_csv(parse_result, name)


if __name__ == "__main__":
    get_all_products()
