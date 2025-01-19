import datetime
import json
import logging
from typing import Union

import numpy as np #https://sky.pro/media/rabota-s-numpy-python/
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger_cashback = logging.getLogger("most_profit_cashback")
logger_invest = logging.getLogger("invest_bank")

def get_top_cashback_categories(transactions: list[dict], year: int, month: Union[int, str]) -> str:
    """
    Возвращает категории с повышенным кэшбэком из списка транзакций за определённый месяц и год.
    """
    try:
        month = int(month)
        if month < 1 or month > 12:
            logger_cashback.warning(f"Некорректный номер месяца: {month}. Укажите месяц от 1 до 12.")
            return "[]"

        if not transactions:
            logger_cashback.warning("Список транзакций пуст.")
            return "[]"

        data = pd.DataFrame(transactions)
        data["datetime"] = pd.to_datetime(data["Дата операции"], dayfirst=True)

        df = data[(data["datetime"].dt.year == year) & (data["datetime"].dt.month == month)]
        data_grouped = df.groupby("Категория").agg({"Кэшбэк": "sum"})

        result_list = []
        df_filtered = (
            data_grouped[data_grouped["Кэшбэк"] != 0]
            .sort_values(by="Кэшбэк", ascending=False)
            .reset_index()
        )

        for _, row in df_filtered.iterrows():
            result_list.append({f"Категория {row['Категория']}": row["Кэшбэк"]})

        logger_cashback.info(f"Сформированы данные о кэшбэке за {month} месяц {year} года.")
        return json.dumps(result_list, ensure_ascii=False)

    except Exception as e:
        logger_cashback.error(f"Ошибка при формировании данных о кэшбэке: {e}.")
        return "[]"

def calculate_investment_potential(transactions: list[dict], month: str, rounding_limit: int) -> float:
    """
    Рассчитывает сумму, которую можно отложить с трат при заданном размере округления.

    Args:
        transactions (list[dict]): Список транзакций.
        month (str): Месяц в формате "YYYY-MM".
        rounding_limit (int): Порог округления.

    Returns:
        float: Сумма, которую можно отложить.
    """
    try:
        if not transactions:
            logger_invest.warning("Список транзакций пуст.")
            return 0.0

        if rounding_limit <= 0:
            logger_invest.warning(f"Некорректное значение порога округления: {rounding_limit}. Укажите положительное число.")
            return 0.0

        data = pd.DataFrame(transactions)
        data["datetime"] = pd.to_datetime(data["Дата операции"], dayfirst=True)

        target_date = datetime.datetime.strptime(month, "%Y-%m")

        filtered_data = data[
            (data["datetime"].dt.year == target_date.year) &
            (data["datetime"].dt.month == target_date.month)
        ]

        if filtered_data.empty:
            logger_invest.info("За указанный месяц транзакции отсутствуют.")
            return 0.0

        pd.options.mode.chained_assignment = None

        filtered_data["Платеж_округл"] = filtered_data["Сумма платежа"].round(-2).abs()
        filtered_data = filtered_data[filtered_data["Сумма платежа"] < 0]

        filtered_data["Сумма платежа"] = -filtered_data["Сумма платежа"]
        filtered_data["Инвесткопилка"] = (
            (filtered_data["Сумма платежа"] / rounding_limit).apply(np.ceil) * rounding_limit - filtered_data["Сумма платежа"]
        )

        total_savings = round(filtered_data["Инвесткопилка"].sum(), 2)
        logger_invest.info(f"Сумма, которую можно отложить: {total_savings} д.ед.")

        return total_savings

    except Exception as e:
        logger_invest.error(f"Ошибка при расчёте суммы для инвесткопилки: {e}.")
        return 0.0
