import json

from src.services import get_profitable_cashback_categories

test_data = [
    {"Дата операции": "01.01.2025 12:00:00", "Категория": "Еда", "Сумма операции": -1000},
    {"Дата операции": "05.01.2025 15:00:00", "Категория": "Техника", "Сумма операции": -2000},
    {"Дата операции": "10.01.2025 09:00:00", "Категория": "Еда", "Сумма операции": -500},
    {"Дата операции": "15.01.2025 10:00:00", "Категория": "Еда", "Сумма операции": -2000},
    {"Дата операции": "20.01.2025 11:00:00", "Категория": "Переводы", "Сумма операции": -1500},
]


def test_profitable_cashback_categories_correct():
    """"""
    result = get_profitable_cashback_categories(test_data, "2025", "01")
    expected_result = {
        "Еда": 35.0,
        "Техника": 20.0,
    }
    assert json.loads(result) == expected_result


def test_profitable_cashback_categories_invalid_year():
    result = get_profitable_cashback_categories(test_data, "20X5", "01")
    assert json.loads(result) == {}


def test_profitable_cashback_categories_invalid_month():
    result = get_profitable_cashback_categories(test_data, "2025", "13")
    assert json.loads(result) == {}


def test_profitable_cashback_categories_empty_data():
    result = get_profitable_cashback_categories([], "2025", "01")
    assert json.loads(result) == {}


def test_profitable_cashback_categories_invalid_date_format():
    invalid_data = [{"Дата операции": "2025-01-01 12:00:00", "Категория": "Еда", "Сумма операции": -1000}]
    result = get_profitable_cashback_categories(invalid_data, "2025", "01")
    assert json.loads(result) == {}


def test_logging_invalid_data_format(caplog):
    with caplog.at_level("ERROR"):
        get_profitable_cashback_categories(test_data, "2025", "XX")
    assert "Передан неверный тип данных для года или месяца" in caplog.text


def test_logging_empty_data(caplog):
    with caplog.at_level("WARNING"):
        get_profitable_cashback_categories([], "2025", "01")
    assert "Передан пустой список данных" in caplog.text
