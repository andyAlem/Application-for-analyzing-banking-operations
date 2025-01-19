import json
from unittest.mock import patch

import pytest

from src.views import main


@pytest.fixture
def mock_data():
    """Пример данных для тестирования."""
    return [
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


@patch("src.views.read_excel_data")
@patch("src.views.greet_user")
@patch("src.views.get_common_transaction_info")
@patch("src.views.get_top_operations")
@patch("src.views.fetch_exchange_rates")
@patch("src.views.fetch_stock_prices")
def test_main_success(
    mock_fetch_stock_prices,
    mock_fetch_exchange_rates,
    mock_get_top_operations,
    mock_get_common_transaction_info,
    mock_greet_user,
    mock_read_excel_data,
    mock_data,
):
    """Тест успешного выполнения функции main."""
    mock_read_excel_data.return_value = mock_data
    mock_greet_user.return_value = "Ho Ho, User!"
    mock_get_common_transaction_info.return_value = {"summary": "info"}
    mock_get_top_operations.return_value = [{"Сумма операции": -200, "Описание": "Magnit"}]
    mock_fetch_exchange_rates.return_value = {"USD": 73.5, "EUR": 86.7}
    mock_fetch_stock_prices.return_value = {"AAPL": 145.3, "GOOGL": 2780.0}

    result = main("2023-01-03 15:25:00")
    result_json = json.loads(result)

    assert "greetings" in result_json
    assert result_json["greetings"] == "Ho Ho, User!"

    assert "cards" in result_json
    assert result_json["cards"] == {"summary": "info"}

    assert "top_transactions" in result_json
    assert len(result_json["top_transactions"]) == 1
    assert result_json["top_transactions"][0]["Сумма операции"] == -200

    assert "currency_rates" in result_json
    assert result_json["currency_rates"] == {"USD": 73.5, "EUR": 86.7}

    assert "stock_prices" in result_json
    assert result_json["stock_prices"] == {"AAPL": 145.3, "GOOGL": 2780.0}


@patch("src.views.read_excel_data")
def test_main_file_not_found(mock_read_excel_data):
    """Тест обработки ситуации, если файл данных не найден."""
    mock_read_excel_data.side_effect = FileNotFoundError("Файл не найден")

    result = main("2023-01-03 15:25:00")
    result_json = json.loads(result)

    assert "Ошибка" in result_json
    assert "Файл не найден" in result_json["Ошибка"]


@patch("src.views.read_excel_data")
def test_main_invalid_date(mock_read_excel_data, mock_data):
    """Тест обработки некорректной даты."""
    mock_read_excel_data.return_value = mock_data

    result = main("неправильная_дата")
    result_json = json.loads(result)

    assert "Ошибка" in result_json
    assert "time data 'неправильная_дата' does not match format" in result_json["Ошибка"]
