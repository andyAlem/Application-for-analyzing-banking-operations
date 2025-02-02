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


def get_profitable_cashback_categories(year: str, month: str, file_name: str = "operations.xlsx",
                                       data_folder: str = "../data/", log_warnings: bool = True) -> str:
    """
    Функция анализирует транзакции, рассчитывает кэшбэк по категориям и выводит результат в формате JSON.
    """
    result = {}

    pattern_year = re.compile(r"\d{4}")
    pattern_month = re.compile(r"\d{2}")

    if not (pattern_year.fullmatch(year) and pattern_month.fullmatch(month)):
        logger.error("Передан неверный тип данных для года или месяца")
        return json.dumps(result)

    try:
        # Загружаем данные из Excel
        data = read_excel_data(file_name, data_folder)
    except ValueError as e:
        logger.error(f"Ошибка при чтении данных: {e}")
        return json.dumps(result)

    if not data:
        logger.warning("Передан пустой список данных")
        return json.dumps(result)

    data_found = False

    for x in data:
        try:
            date_obj = datetime.strptime(x["Дата операции"], "%d.%m.%Y %H:%M:%S")
        except ValueError:
            logger.warning(f"Неверный формат даты: {x['Дата операции']}")
            continue

        year_part = date_obj.strftime("%Y")
        month_part = date_obj.strftime("%m")

        if year_part == year and month_part == month:
            data_found = True
            category = x.get("Категория")
            amount = x.get("Сумма операции")

            if category and amount and category != "Переводы" and amount < 0:
                if category not in result:
                    result[category] = 0.0
                result[category] += abs(amount) * 0.01

        elif log_warnings:
            logger.warning(f"Дата операции ({date_obj}) не совпадает с запросом (Год: {year}, Месяц: {month})")

    if not data_found:
        logger.warning(f"Нет транзакций за {year}-{month}. Проверьте данные.")

    filtered_result = dict(sorted(result.items(), key=lambda value: value[1], reverse=True))

    logger.info("Приводим результат к формату json")
    parsed_result = json.dumps(filtered_result, ensure_ascii=False)

    return parsed_result


# print(get_profitable_cashback_categories("2021", "12", file_name="operations.xlsx",
#                                           data_folder="/home/andrej/Poetry_homework/PythonProject/PythonProject/Project 1. Application for analyzing banking operations/data/",
#                                           log_warnings=False))
