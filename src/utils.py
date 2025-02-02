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

        # Замена NaN на "Unknown" или 0
        df["Номер карты"] = df["Номер карты"].fillna("Unknown").str.replace("*", "", regex=False)

        if "Кэшбэк" not in df.columns:
            df["Кэшбэк"] = 0

        df["Кэшбэк"] = df["Кэшбэк"].fillna(0).round(2)
        df["MCC"] = df["MCC"].fillna(0).astype(int)

        if "Сумма операции" in df.columns:
            df["Сумма операции"] = df["Сумма операции"].round(2)  # Округление до двух знаков после запятой

        return df.to_dict(orient="records")

    except Exception as e:
        raise ValueError(f"Ошибка при чтении файла {file_path}: {e}")


def get_top_operations(transactions: list[dict], top_n: int = 5) -> list[dict]:
    """
    Функция возвращает топ операций, отсортированных по сумме.
    """
    try:
        df = pd.DataFrame(transactions)

        df["Номер карты"] = df["Номер карты"].fillna("Unknown")

        if "Кэшбэк" not in df.columns:
            df["Кэшбэк"] = 0

        df["Кэшбэк"] = df["Кэшбэк"].fillna(0).round(2)

        df["MCC"] = df["MCC"].fillna(0).astype(int)

        if "Дата операции" in df.columns and isinstance(df["Дата операции"].iloc[0], str):
            df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce")

        df["Дата операции"] = df["Дата операции"].fillna("Unknown")

        top_transactions = df.sort_values(by="Сумма операции", ascending=False).head(top_n)

        result = []
        for _, row in top_transactions.iterrows():
            date_str = row["Дата операции"] if row["Дата операции"] != "Unknown" else "Unknown"

            result.append(
                {
                    "date": date_str if isinstance(date_str, str) else date_str.strftime("%d.%m.%Y"),
                    "amount": f"{row['Сумма операции']:.2f}",
                    "category": row.get("Категория", "Unknown"),
                    "description": row.get("Описание", "Unknown"),
                }
            )

        return result

    except Exception as e:
        raise ValueError(f"Ошибка при получении ТОП-операций: {e}")


def get_common_transaction_info(transactions: list[dict]) -> list[dict]:
    """
    Функция возвращает общую информацию по транзакциям, суммируя их по картам.
    Рассчитывает общую потраченную сумму и процент кэшбэка по каждой карте.
    """
    try:
        card_info = {}

        for transaction in transactions:
            last_digits = transaction.get("Номер карты", "Unknown")
            total_spent = transaction.get("Сумма операции", 0)
            cashback = transaction.get("Кэшбэк", 0)

            if not isinstance(total_spent, (int, float)):
                total_spent = 0
            if not isinstance(cashback, (int, float)):
                cashback = 0

            if last_digits not in card_info:
                card_info[last_digits] = {"total_spent": 0, "cashback_sum": 0, "count": 0}

            card_info[last_digits]["total_spent"] += total_spent
            card_info[last_digits]["cashback_sum"] += cashback
            card_info[last_digits]["count"] += 1

        result = []

        for card_number, data in card_info.items():
            total_spent = data["total_spent"]
            cashback_sum = data["cashback_sum"]
            cashback_percentage = (cashback_sum / abs(total_spent)) * 100 if total_spent != 0 else 0
            cashback_percentage = 0.0 if cashback_percentage == -0.0 else cashback_percentage

            if cashback_percentage == 0.0:
                cashback_percentage = 0

            result.append(
                {
                    "last_digits": "" if card_number == "Unknown" else card_number[-4:],
                    "total_spent": round(abs(total_spent), 2),
                    "cashback_percentage": round(cashback_percentage, 2),
                }
            )

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
