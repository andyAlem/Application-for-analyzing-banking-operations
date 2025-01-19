import json
import logging
import os
from datetime import datetime
import pandas as pd
import requests
from dotenv import load_dotenv
import ssl
import certifi

from urllib.request import urlopen

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

        # Чтение файла Excel
        data = pd.read_excel(file_path)

        # Приводим столбцы к нужным типам
        data["Номер карты"] = data["Номер карты"].astype(str).str.replace('*', '')  # Убираем звездочки
        data["Сумма операции"] = pd.to_numeric(data["Сумма операции"], errors='coerce')  # Преобразуем в числовой формат
        data["Сумма операции"] = data["Сумма операции"].fillna(0)  # Заменяем NaN на 0

        logger.info(f"Файл успешно прочитан: {file_name}")
        return data.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Ошибка чтения файла {file_name}. Ошибка: {e}")
        return []


def get_top_operations(transactions: list[dict], top_n: int = 5) -> list[dict]:
    """
    Функция возвращает топ N крупных операций из столбца "Сумма операции".
    """
    try:
        df = pd.DataFrame(transactions)
        required_columns = {"Дата операции", "Сумма операции", "Номер карты", "Категория", "Описание"}
        if not required_columns.issubset(df.columns):
            logger.error("Отсутствуют необходимые столбцы в данных.")
            return []

        # Преобразуем данные к числовому типу (на случай ошибок в исходных данных)
        df["Сумма операции"] = pd.to_numeric(df["Сумма операции"], errors='coerce')

        # Сортировка данных по "Сумма операции" в порядке убывания
        df = df.sort_values(by="Сумма операции", ascending=False)

        # Получаем топ операций
        top_operations = df.head(top_n).to_dict(orient="records")

        logger.info("Операции успешно обработаны.")
        return top_operations
    except Exception as e:
        logger.error(f"Ошибка обработки операций: {e}")
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


def fetch_exchange_rates(settings_file: str, data_folder: str = "../data/") -> list[dict]:
    """
    Функция получает json-файл с кодировкой иностранных валют и url-ссылку по обменным курсам валют и
    возвращает значения текущих котировок этих валют
    """
    try:
        # Загрузка данных из файла настроек
        config_path = os.path.join(data_folder, settings_file)
        if not os.path.exists(config_path):
            logger.error(f"Файл отсутствует {config_path}.")
            return []

        with open(config_path, "r", encoding="utf-8") as file:
            user_config = json.load(file)

        currencies = user_config.get("user_currencies", [])

        # Получаем данные с API Центрального банка РФ
        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        exchange_data = response.json()

        # Собираем результаты для запрашиваемых валют
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

        # Загрузка данных из файла настроек
        config_path = os.path.join(data_folder, settings_file)
        if not os.path.exists(config_path):
            logger.error(f"Файл отсутствует {config_path}.")
            return []

        with open(config_path, "r", encoding="utf-8") as file:
            user_config = json.load(file)

        stocks = user_config.get("user_stocks", [])

        # Создаем SSL-контекст
        ssl_context = ssl.create_default_context(cafile=certifi.where())

        # Запрашиваем данные о котировках акций через API
        url = f"https://financialmodelingprep.com/api/v3/stock/list?apikey={api_key}"
        response = urlopen(url, context=ssl_context)  # Используем context вместо cafile
        stock_data = json.loads(response.read().decode("utf-8"))

        # Собираем результат по акциям
        result = [
            {"stock": stock, "price": next((item["price"] for item in stock_data if item["symbol"] == stock), None)}
            for stock in stocks
        ]

        logger.info("Успешно обработано.")
        return result
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return []
