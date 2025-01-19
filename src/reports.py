import logging
import os
from datetime import datetime
from typing import Optional

import pandas as pd
from dateutil.relativedelta import relativedelta

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger("spending_by_weekday")


def print_spending_by_date(func):
    """Декоратор для записи результата функции в файл report_1.txt."""
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        with open(os.path.join("./print_decorators/report_1.txt"), "w") as file:
            file.write(result.to_string(header=False))
        return result
    return wrapper


def print_name_spending_by_date(file_name: str):
    """Декоратор для записи результата функции в указанный файл."""
    def my_decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            with open(os.path.join(f"./print_decorators/{file_name}"), "w") as file:
                file.write(result.to_string(header=False))
            return result
        return wrapper
    return my_decorator


def spending_by_weekday(transactions: pd.DataFrame, date: Optional[str] = None) -> str:
    """
    Возвращает средние траты в каждый из дней недели за последние три месяца.
    """
    try:
        if date is None:
            date = datetime.now()
        else:
            date = datetime.strptime(date, "%Y-%m-%d")

        transactions["datetime"] = pd.to_datetime(transactions["Дата операции"], dayfirst=True)
        transactions["day_name"] = transactions["datetime"].dt.day_name()

        filtered_transactions = transactions[
            (transactions["datetime"] >= (date + relativedelta(months=-3))) & (transactions["datetime"] <= date)
        ]

        grouped = filtered_transactions.groupby(by="day_name")
        result = grouped["Сумма платежа"].mean().abs().round(2)

        logger.info("Успешное формирование отчета о средних тратах по дням недели.")
        return result.to_json()

    except Exception as e:
        logger.error(f"Не удалось сформировать отчет. Ошибка: {e}")
        return "{}"
