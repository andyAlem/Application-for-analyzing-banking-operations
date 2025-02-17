import logging
import os
from datetime import datetime
from typing import Optional

import pandas as pd
from dateutil.relativedelta import relativedelta

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger("spending_by_weekday")


def print_spending_by_date(func):
    """Декоратор для записи результата функции в файл с названием по умолчанию (report.txt)."""

    def wrapper(*args, **kwargs):
        logger.info(f"Вызов функции {func.__name__} для записи отчета в файл report.txt")
        result = func(*args, **kwargs)

        os.makedirs("./reports", exist_ok=True)

        with open(os.path.join("./reports/report.txt"), "w") as file:
            file.write(result)

        logger.info(f"Отчет записан в файл report.txt")
        return result

    return wrapper


def print_name_spending_by_date(file_name: str = "file.log"):
    """Декоратор для записи результата функции в указанный файл (или по умолчанию)."""

    def wrapper(func):
        def inner(*args, **kwargs):
            try:
                logger.info(f"Вызов функции {func.__name__} для записи отчета в файл {file_name}")
                result = func(*args, **kwargs)

                os.makedirs(f"./reports", exist_ok=True)

                with open(os.path.join(f"./reports/{file_name}"), "w") as file:
                    file.write(result)

                logger.info(f"Отчет записан в файл {file_name}")
                return result

            except Exception as error:
                logger.error(f"Ошибка при выполнении функции {func.__name__}: {error}")

                os.makedirs(f"./reports", exist_ok=True)

                with open(os.path.join(f"./reports/{file_name}"), "w") as file:
                    file.write(f"Ошибка: {error}")

                return "{}"

        return inner

    return wrapper


@print_name_spending_by_date(file_name="custom_spending_report.txt")
@print_spending_by_date
def spending_by_weekday(transactions: pd.DataFrame, date: Optional[str] = None) -> str:
    """
    Возвращает средние траты в каждый из дней недели за последние три месяца.
    """
    try:
        if date is None:
            date = datetime.now()
        else:
            date = datetime.strptime(date, "%Y-%m-%d")

        date = date.replace(hour=0, minute=0, second=0, microsecond=0)

        transactions["datetime"] = pd.to_datetime(transactions["Дата операции"], format="%Y-%m-%d")
        transactions["day_name"] = transactions["datetime"].dt.day_name()

        filtered_transactions = transactions[
            (transactions["datetime"] >= (date + relativedelta(months=-3))) & (transactions["datetime"] <= date)
        ]

        logger.info(f"Количество транзакций после фильтрации: {len(filtered_transactions)}")

        if len(filtered_transactions) == 0:
            logger.warning("Не найдено транзакций за последние 3 месяца.")

        grouped = filtered_transactions.groupby(by="day_name")
        result = grouped["Сумма платежа"].mean().abs().round(2).sort_index()

        logger.info(f"Результат отчета: {result}")

        if result.empty:
            logger.warning("Результат отчета пуст.")

        return result.to_json()

    except Exception as e:
        logger.error(f"Не удалось сформировать отчет. Ошибка: {e}")
        return "{}"
