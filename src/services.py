import json
import logging
import re
from datetime import datetime

logger = logging.getLogger("my_log")
logger.setLevel(logging.WARNING)
file_handler = logging.FileHandler("logfile.log", mode="w", encoding="utf-8")
file_formatter = logging.Formatter("%(asctime)s - %(filename)s - %(levelname)s: %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


def get_profitable_cashback_categories(data: list, year: str, month: str) -> str:
    """
    На вход функции поступают данные для анализа, год и месяц.
    """
    result = {}

    pattern_year = re.compile(r"\d{4}")
    pattern_month = re.compile(r"\d{2}")

    if not (pattern_year.fullmatch(year) and pattern_month.fullmatch(month)):
        logger.error("Передан неверный тип данных для года или месяца")
        return json.dumps(result)

    if not data:
        logger.warning("Передан пустой список данных")
        return json.dumps(result)

    for x in data:
        try:
            date_obj = datetime.strptime(x["Дата операции"], "%d.%m.%Y %H:%M:%S")
        except ValueError:
            logger.warning(f"Неверный формат даты: {x['Дата операции']}")
            continue

        year_part = date_obj.strftime("%Y")
        month_part = date_obj.strftime("%m")

        if year_part == year and month_part == month:
            category = x["Категория"]
            amount = x["Сумма операции"]

            if category != "Переводы" and amount < 0:
                if category not in result:
                    result[category] = 0.0
                result[category] += abs(amount) * 0.01
        else:
            logger.warning("Дата операции отличается от запроса")

    logger.info("Приводим результат к формату json")
    filtered_result = dict(sorted(result.items(), key=lambda value: value[1], reverse=True))
    parsed_result = json.dumps(filtered_result, ensure_ascii=False)

    return parsed_result
