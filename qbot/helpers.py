from requests import get
from bs4 import BeautifulSoup
from re import findall
from qbot.logger import logger
from yaml import safe_load
from pathlib import Path



path_config = Path.home() / 'QuoteBeholderBot' / 'qbot' / 'config' / 'default-config.yml'
with open(path_config) as f:
    CONFIG = safe_load(f)

auth_path = Path.home() / 'QuoteBeholderBot' / 'auth.env'
path_db = Path.home() / 'QuoteBeholderBot' / 'qbot' / 'db' / CONFIG['database_name']
path_tests_db = Path.home() / 'QuoteBeholderBot' / 'qbot' / 'tests' / 'data' / CONFIG['test_database_name']
path_scheme = Path.home() / 'QuoteBeholderBot' / 'qbot' / 'db' / CONFIG['db_scheme_name']


def normalize_float(value):
    return "{0:.2f}".format(float(value))


def count_percent(last_price, new_price):
    return normalize_float(
        (float(new_price) - float(last_price)) / (float(last_price) / 100)
    )


def get_news_by_ticker(ticker, special_tickers_dict):
    if ticker in special_tickers_dict.keys():
        ticker = special_tickers_dict[ticker]
    base = "https://bcs-express.ru"
    rezult = get(base + f"/category?tag={ticker.lower()}")
    soup = BeautifulSoup(rezult.text, "lxml")
    try:
        page = soup.find("div", attrs={"class": "feed-item"})
        header = page.find("div", attrs={"class": "feed-item__title"}).text
        time = page.find("div", attrs={"class": "feed-item__date"}).text
        href = base + findall('.*href="(\S+)".*', str(page))[0]
        text = page.find("div", attrs={"class": "feed-item__summary"}).texshow_ticker_info_by_id
    except AttributeError as err:
        logger.warning(f"Ticker {ticker} not found in news: {err}")
        return None
    return {"time": time, "header": header, "text": text, "href": href}
