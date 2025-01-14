import datetime
import json
from json.decoder import JSONDecodeError
import os
import urllib.request
from typing import Any, Dict, List

import pandas as pd
import requests
import logging
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(filename)s - %(levelname)s - %(message)s",
    filename="../logs/utills.log",
    filemode="w",
)

logger = logging.getLogger()

load_dotenv()
API_KEY_CUR = os.getenv("API_KEY_CUR")
SP_500_API_KEY = os.getenv("SP_500_API_KEY")

date_now = datetime.datetime.now()



def greeting_by_time_of_day(current_time: datetime) -> str:
    """Функция выводит различное приветствие"""
    logger.info('Начало работы функции вывода приветствия')
    hour = current_time.hour
    if 6 <= hour < 12:
        return "Доброе утро!"
    elif 12 <= hour < 18:
        return "Добрый день!"
    elif 18 <= hour < 23:
        return "Добрый вечер!"
    return "Доброй ночи!"


def filter_by_date(date: str, my_list: list) -> list:
    """Функция фильтрующая данные по заданной дате"""
    if not date:
        return []

    year, month, day = map(int, date.split('-'))
    date_obj = datetime.date(year, month, day)

    filtered = [
        i for i in my_list
        if isinstance(i.get("Дата платежа"), str) and i["Дата платежа"] != "nan" and
           date_obj == datetime.datetime.strptime(i["Дата платежа"], "%d.%m.%Y").date()
    ]
    return filtered


def get_excel_file(file_excel: str) -> List[Dict[str, Any]]:
    """Функция обрабатывает excel файл и возвращает список словарей"""
    try:
        df = pd.read_excel(file_excel)
        result = df.apply(
            lambda row: {col: row[col] for col in df.columns}, axis=1
        ).tolist()
        return result
    except FileNotFoundError as e:
        logger.error(f"Файл с транзакциями не найден: {e}")
        return []


def card_expenses(my_list: list) -> List[Dict[str, Any]]:
    """Функция выводит последние 4 цифры карты, сумму расходов и кешбэк"""
    cards = {}
    for transaction in my_list:
        card_number = str(transaction["Номер карты"])[-4:]
        amount = transaction["Сумма платежа"]
        if card_number and amount not in ["nan", None]:
            cards[card_number] = cards.get(card_number, 0) + float(amount)

    return [{"last_digits": k, "total_spent": round(v, 2), "cashback": round(v / 100, 2)} for k, v in cards.items()]


def transaction_rating_by_amount(my_list: list) -> List[Dict[str, Any]]:
    """Функция выводит топ-5 транзакций по сумме платежа"""
    sorted_transactions = sorted(
        [t for t in my_list if t["Категория"] != "Пополнения"],
        key=lambda x: x["Сумма платежа"],
        reverse=True
    )[:5]

    return [{
        "date": transaction["Дата платежа"],
        "amount": transaction["Сумма платежа"],
        "category": transaction["Категория"],
        "description": transaction["Описание"]
    } for transaction in sorted_transactions]


def exchange_rate(currency: dict) -> List[Dict[str, Any]]:
    """Функция выводит актуальную информацию о курсе валют"""
    result = []
    for i in currency:
        url = f"https://v6.exchangerate-api.com/v6/{API_KEY_CUR}/latest/{i}"
        try:
            with urllib.request.urlopen(url) as response:
                body_dict = json.loads(response.read())
                result.append({
                    "currency": i,
                    "rate": round(body_dict["conversion_rates"]["RUB"], 2)
                })
        except urllib.error.URLError as e:
            logger.error(f"Ошибка при получении данных о валюте {i}: {e}")

    return result


def get_price_stock(stocks: dict) -> List[Dict[str, Any]]:
    """Функция для получения данных об акциях из списка S&P500"""
    stock_prices = []
    for stock in stocks:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stock}&apikey={SP_500_API_KEY}"
        try:
            response = requests.get(url, timeout=5, allow_redirects=False)
            result = response.json()
            stock_prices.append({
                "stock": stock,
                "price": round(float(result["Global Quote"]["05. price"]), 2)
            })
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при получении данных о акции {stock}: {e}")

    return stock_prices


def get_user_settings_from_json(path: str) -> Dict[str, Any]:
    """Функция принимает на вход путь до JSON-файла и возвращает данные по валюте и акциях"""
    try:
        with open(path, encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, JSONDecodeError) as e:
        logger.error(f"Ошибка при загрузке файла настроек: {e}")
        return {}
