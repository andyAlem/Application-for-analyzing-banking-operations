import json
import logging
import os
from datetime import datetime
from urllib.request import urlopen
import certifi

import pandas as pd
import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("transaction_analysis")


def read_excel_data(file_name: str, data_folder: str = "../data/") -> list[dict]:
    """
    Функция считывает данные из excel файла и возвращает в формате df
    """
    try:
        file_path = os.path.join(data_folder, file_name)
        if not os.path.exists(file_path):
            logger.error(f"Файл {file_path} не существует.")
            return []

        data = pd.read_excel(file_path)
        logger.info(f"Файл успешно прочитан: {file_name}")
        return data.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Ошибка чтения файла {file_name}. Ошибка: {e}")
        return []


def get_top_operations(transactions: list[dict], top_n: int = 5) -> list[dict]:
    """
    Функция возвращает топ 5 крупных операций из столбца "Сумма операции"
    """
    try:
        df = pd.DataFrame(transactions)
        required_columns = {"Дата операции", "Сумма операции", "Номер карты", "Категория", "Описание"}
        if not required_columns.issubset(df.columns):
            logger.error("Столбец не найден.")
            return []

        df = df.sort_values(by="Сумма операции", ascending=False)
        top_operations = df.head(top_n).to_dict(orient="records")

        logger.info("Операции успешно загружены.")
        return top_operations
    except Exception as e:
        logger.error(f"Ошибка загрузки операций. Ошибка: {e}")
        return []


def get_common_transaction_info(transactions: list[dict]) -> list[dict]:
    """
    Функция возвращает общую информацию по транзакциям
    """
    try:
        df = pd.DataFrame(transactions)
        required_columns = {"Номер карты", "Сумма операции", "Кэшбэк"}
        if not required_columns.issubset(df.columns):
            logger.error("Столбец отсутствует .")
            return []

        df_grouped = df.groupby("Номер карты").agg({"Сумма операции": "sum", "Кэшбэк": "sum"}).reset_index()
        df_grouped["Сумма операции"] = df_grouped["Сумма операции"].abs()

        result = []
        for _, row in df_grouped.iterrows():
            total_spent = row["Сумма операции"]
            cashback_percentage = round(row["Кэшбэк"] / total_spent * 100, 2) if total_spent > 0 else 0
            result.append({
                "last_digits": str(row["Номер карты"])[-4:],
                "total_spent": total_spent,
                "cashback_percentage": cashback_percentage,
            })

        logger.info("Успешно обработана информация.")
        return result
    except Exception as e:
        logger.error(f"Ошибка обработки. Ошибка: {e}")
        return []


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


def fetch_exchange_rates(currency_config_file: str, data_folder: str = "../data/") -> list[dict]:
    """
    Функция получает json-файл с кодировкой иностранных валют и url-ссылку по обменным курсам валют и
    возвращает значения текущих котировок этих валют
    """
    try:
        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        exchange_data = response.json()

        config_path = os.path.join(data_folder, currency_config_file)
        if not os.path.exists(config_path):
            logger.error(f"Файл отсутствует {config_path}.")
            return []

        with open(config_path, "r", encoding="utf-8") as file:
            user_config = json.load(file)

        currencies = user_config.get("user_currencies", [])
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


def fetch_stock_prices(stock_config_file: str, data_folder: str = "../data/") -> list[dict]:
    """
    Функция получает json-файл с наименованиями ценных бумаг и url-ссылку на котировки ценных бумаг и
    возвращает их текущие котировки
    """
    try:
        load_dotenv()
        api_key = os.getenv("API_KEY")
        if not api_key:
            logger.error("API_KEY not found in environment variables.")
            return []

        url = f"https://financialmodelingprep.com/api/v3/stock/list?apikey={api_key}"
        response = urlopen(url, cafile=certifi.where())
        stock_data = json.loads(response.read().decode("utf-8"))

        config_path = os.path.join(data_folder, stock_config_file)
        if not os.path.exists(config_path):
            logger.error(f"Файл отсутствует {config_path}.")
            return []

        with open(config_path, "r", encoding="utf-8") as file:
            user_config = json.load(file)

        stocks = user_config.get("user_stocks", [])
        result = [
            {"stock": stock, "price": next((item["price"] for item in stock_data if item["symbol"] == stock), None)}
            for stock in stocks
        ]

        logger.info("Успешно обработан.")
        return result
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return []
