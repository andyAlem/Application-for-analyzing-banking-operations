import json
import logging
import os
import ssl
from datetime import datetime
from urllib.request import urlopen

import certifi
import pandas as pd
import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("transaction_analysis")

load_dotenv()


def read_excel_data(file_name: str, data_folder: str = "../data/") -> list[dict]:
    """
    Функция считывает данные из excel файла и возвращает в формате df
    """
    try:
        file_path = os.path.join(data_folder, file_name)
        if not os.path.exists(file_path):
            logger.error(f"Файл {file_path} не существует.")
            return []

        df = pd.read_excel(file_path)

        df["Номер карты"] = df["Номер карты"].fillna("Unknown")# Замена NaN на "Unknown" или 0
        df["Кэшбэк"] = df["Кэшбэк"].fillna(0).round(2)
        df["MCC"] = df["MCC"].fillna(0).astype(int)

        if "Сумма операции" in df.columns:
            df["Сумма операции"] = df["Сумма операции"].round(2) # Округление до двух знаков после запятой

        return df.to_dict(orient="records")

    except Exception as e:
        raise ValueError(f"Ошибка при чтении файла {file_path}: {e}")


def get_top_operations(transactions: list[dict], top_n: int = 5) -> list[dict]:
    """
    Функция возвращает топ N крупных операций из столбца "Сумма операции".
    """
    try:
        df = pd.DataFrame(transactions)

        # Замена NaN значений
        df["Номер карты"] = df["Номер карты"].fillna("Unknown")
        df["Кэшбэк"] = df["Кэшбэк"].fillna(0).round(2)
        df["MCC"] = df["MCC"].fillna(0).astype(int)

        required_columns = [
            "Дата операции", "Дата платежа", "Номер карты", "Статус", "Сумма операции",
            "Валюта операции", "Сумма платежа", "Валюта платежа", "Кэшбэк", "Категория",
            "MCC", "Описание", "Бонусы (включая кэшбэк)", "Округление на инвесткопилку",
            "Сумма операции с округлением", "datetime"
        ]

        df = df[required_columns]

        top_transactions = df.sort_values(by="Сумма операции", ascending=False).head(5)

        return top_transactions.to_dict(orient="records")

    except Exception as e:
        raise ValueError(f"Ошибка при получении ТОП-операций: {e}")


def get_common_transaction_info(transactions: list[dict]) -> list[dict]:
    """
    Функция возвращает общую информацию по транзакциям
    """
    try:
        result = []
        for transaction in transactions:
            last_digits = transaction.get("Номер карты", "Unknown")
            total_spent = round(transaction.get("Сумма операции", 0), 2)
            cashback_percentage = round(transaction.get("Кэшбэк", 0), 2)

            result.append({
                "last_digits": last_digits,
                "total_spent": total_spent,
                "cashback_percentage": cashback_percentage
            })

        return result

    except Exception as e:
        raise ValueError(f"Ошибка при обработке транзакций: {e}")


def greet_user() -> str:
    """
    Приветствие пользователя
    """
    current_hour = datetime.now().hour
    if 6 < current_hour <= 10:
        return "Доброе утро!"
    elif 11 <= current_hour <= 16:
        return "Доброго дня!"
    elif 17 <= current_hour <= 21:
        return "Доброго вечера!"
    else:
        return "Доброй ночи!"


def fetch_exchange_rates(settings_file: str, data_folder: str = "../data/") -> list[dict]:
    """
    Функция получает json-файл с кодировкой иностранных валют и url-ссылку по обменным курсам валют и
    возвращает значения текущих котировок этих валют
    """
    try:
        config_path = os.path.join(data_folder, settings_file)
        if not os.path.exists(config_path):
            logger.error(f"Файл отсутствует {config_path}.")
            return []

        with open(config_path, "r", encoding="utf-8") as file:
            user_config = json.load(file)

        currencies = user_config.get("user_currencies", [])

        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        exchange_data = response.json()

        result = [
            {"currency": currency, "exchange_rate": exchange_data["Valute"].get(currency, {}).get("Value")}
            for currency in currencies
            if currency in exchange_data["Valute"]
        ]

        logger.info("Успешно обработано.")
        return result
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return []


def fetch_stock_prices(settings_file: str, data_folder: str = "../data/") -> list[dict]:
    """
    Функция получает json-файл с тикерами акций и API для получения котировок этих акций.
    """
    try:
        load_dotenv()
        api_key = os.getenv("API_KEY")
        if not api_key:
            logger.error("API_KEY не найден.")
            return []

        config_path = os.path.join(data_folder, settings_file)
        if not os.path.exists(config_path):
            logger.error(f"Файл отсутствует {config_path}.")
            return []

        with open(config_path, "r", encoding="utf-8") as file:
            user_config = json.load(file)

        stocks = user_config.get("user_stocks", [])

        ssl_context = ssl.create_default_context(cafile=certifi.where())

        url = f"https://financialmodelingprep.com/api/v3/stock/list?apikey={api_key}"
        response = urlopen(url, context=ssl_context)  # Используем context вместо cafile
        stock_data = json.loads(response.read().decode("utf-8"))

        result = [
            {"stock": stock, "price": next((item["price"] for item in stock_data if item["symbol"] == stock), None)}
            for stock in stocks
        ]

        logger.info("Успешно обработано.")
        return result
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return []
