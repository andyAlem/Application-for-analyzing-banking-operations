import json
import os

import pandas as pd

from src.utils import (fetch_exchange_rates, fetch_stock_prices,
                       get_common_transaction_info, get_top_operations,
                       greet_user, read_excel_data)


def test_read_excel_data():
    test_data = pd.DataFrame(
        {
            "Номер карты": ["*1234", "*5678"],
            "Сумма операции": [-100.50, -200.75],
            "Категория": ["Супермаркеты", "Фастфуд"],
        }
    )
    test_file = "test_data.xlsx"
    test_data.to_excel(test_file, index=False)

    try:
        result = read_excel_data(test_file, data_folder="./")
        assert isinstance(result, list), "Результат должен быть списком"
        assert len(result) == 2, "Должно быть две строки данных"
        assert result[0]["Номер карты"] == "1234", "Звездочки должны быть удалены"
        assert result[1]["Сумма операции"] == -200.75, "Сумма операции должна быть корректной"
    finally:
        os.remove(test_file)  # Удаляем тестовый файл


def test_get_top_operations():
    transactions = [
        {
            "Дата операции": "2023-01-01",
            "Сумма операции": -150,
            "Номер карты": "1234",
            "Категория": "Фастфуд",
            "Описание": "McDonald's",
        },
        {
            "Дата операции": "2023-01-02",
            "Сумма операции": -200,
            "Номер карты": "5678",
            "Категория": "Супермаркеты",
            "Описание": "Magnit",
        },
        {
            "Дата операции": "2023-01-03",
            "Сумма операции": -100,
            "Номер карты": "1234",
            "Категория": "Фастфуд",
            "Описание": "KFC",
        },
    ]
    result = get_top_operations(transactions, top_n=2)
    assert len(result) == 2, "Должны вернуться только две операции"
    assert result[0]["Сумма операции"] == -100, "Самая крупная операция должна быть первой"
    assert result[1]["Сумма операции"] == -150, "Вторая по величине операция должна быть второй"


def test_get_common_transaction_info():
    transactions = [
        {"Номер карты": "1234", "Сумма операции": -150, "Кэшбэк": 10},
        {"Номер карты": "1234", "Сумма операции": -100, "Кэшбэк": 5},
        {"Номер карты": "5678", "Сумма операции": -200, "Кэшбэк": 20},
    ]
    result = get_common_transaction_info(transactions)
    assert len(result) == 2, "Должны быть данные для двух карт"
    assert result[0]["last_digits"] == "1234", "Номер карты должен быть корректным"
    assert result[0]["total_spent"] == 250, "Общая сумма операций должна быть положительной"
    assert result[0]["cashback_percentage"] == 6.0, "Процент кэшбэка должен быть корректным"


def test_greet_user():
    result = greet_user()
    assert result in [
        "Доброе утро!",
        "Доброго дня!",
        "Доброго вечера!",
        "Доброй ночи!",
    ], "Приветствие должно быть корректным"


def test_fetch_exchange_rates():
    test_settings = {"user_currencies": ["USD", "EUR"]}
    test_file = "test_settings.json"
    with open(test_file, "w", encoding="utf-8") as file:
        json.dump(test_settings, file)

    try:
        result = fetch_exchange_rates(test_file, data_folder="./")
        assert isinstance(result, list), "Результат должен быть списком"
        assert all(
            "currency" in item and "exchange_rate" in item for item in result
        ), "Каждый элемент должен содержать валюту и курс"
    finally:
        os.remove(test_file)


def test_fetch_stock_prices():
    test_settings = {"user_stocks": ["AAPL", "GOOGL"]}
    test_file = "test_settings.json"
    with open(test_file, "w", encoding="utf-8") as file:
        json.dump(test_settings, file)

    try:
        result = fetch_stock_prices(test_file, data_folder="./")
        assert isinstance(result, list), "Результат должен быть списком"
        assert all(
            "stock" in item and "price" in item for item in result
        ), "Каждый элемент должен содержать акцию и цену"
    finally:
        os.remove(test_file)
