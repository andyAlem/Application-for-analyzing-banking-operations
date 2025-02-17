import json
import logging
import re
from datetime import datetime

from src.utils import read_excel_data

logger = logging.getLogger("my_log")
logger.setLevel(logging.WARNING)
file_handler = logging.FileHandler("logfile.log", mode="w", encoding="utf-8")
file_formatter = logging.Formatter("%(asctime)s - %(filename)s - %(levelname)s: %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


def get_profitable_cashback_categories(
    year: str, month: str, file_name: str = "operations.xlsx", data_folder: str = "../data/"
) -> str:
    """
    На вход функции поступают год и месяц для анализа.
    На выходе — JSON с анализом, сколько на каждой категории можно заработать кешбэка.
    """
    filtered_data = []
    result = {}

    pattern_year = re.compile(r"\d{4}")
    pattern_month = re.compile(r"\d{2}")

    logger.info("Проверка на корректность введенных данных")

    if pattern_year.fullmatch(year) and pattern_month.fullmatch(month):
        try:
            # Чтение данных из Excel-файла
            logger.info(f"Чтение данных из файла {file_name}")
            data = read_excel_data(file_name, data_folder)
        except Exception as e:
            logger.error(f"Ошибка при чтении данных: {e}")
            return "{}"

        if data and 12 >= int(month) > 0:
            logger.info("Начало обработки транзакций")
            for x in data:
                try:
                    date_obj = datetime.strptime(x["Дата операции"], "%d.%m.%Y %H:%M:%S")
                    year_part = date_obj.strftime("%Y")
                    month_part = date_obj.strftime("%m")

                    logger.info("Проверка операции на совпадение месяца и года для поиска")

                    if year_part == year and month_part == month:
                        logger.info("Добавление подходящих операций в новый список")
                        filtered_data.append(x)
                        category = x["Категория"]
                        amount = x["Сумма операции"]

                        if category not in result and amount < 0:
                            if category != "Переводы":
                                result[category] = 0.0

                                logger.info("Формирование результата с категориями и подсчет кэшбека")
                                result[category] += abs(amount * 0.01)

                    else:
                        logger.warning("Дата операции отличается от запроса")

                except ValueError as e:
                    logger.warning(f"Неверный формат даты: {x['Дата операции']}")
                    continue

        else:
            logger.error("Некорректный месяц или отсутствуют данные")
            return "{}"

    else:
        logger.error("Передан неверный формат года или месяца")
        return "{}"

    logger.info("Приводим результат к формату json")

    rounded_result = {category: round(cashback, 2) for category, cashback in result.items()}
    filtered_result = dict(sorted(rounded_result.items(), key=lambda value: value[1], reverse=True))
    parsed_result = json.dumps(filtered_result, ensure_ascii=False)

    return parsed_result
