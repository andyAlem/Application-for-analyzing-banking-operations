import json
from unittest.mock import patch

import pytest

from src.services import get_profitable_cashback_categories


def test_get_profitable_cashback_categories_calculation(sample_data_services):
    """Тестирует корректность расчета кэшбэка по категориям."""
    with patch("src.services.read_excel_data", return_value=sample_data_services):
        result = get_profitable_cashback_categories("2021", "12")
        result_dict = json.loads(result)
        assert result_dict == {
            "Супермаркеты": 10.0,
            "Рестораны": 5.0,
            "Транспорт": 3.0,
        }


def test_get_profitable_cashback_categories_empty_data():
    """Проверяет, что возвращается пустой JSON, если данных нет."""
    with patch("src.services.read_excel_data", return_value=[]):
        result = get_profitable_cashback_categories("2021", "12")
        assert result == "{}"


def test_get_profitable_cashback_categories_invalid_date():
    """Проверяет, что возвращается пустой JSON, если дата некорректна"""
    invalid_data = [
        {"Дата операции": "invalid_date", "Категория": "Супермаркеты", "Сумма операции": -1000},
    ]
    with patch("src.services.read_excel_data", return_value=invalid_data):
        result = get_profitable_cashback_categories("2021", "12")
        assert result == "{}"


def test_get_profitable_cashback_categories_invalid_year_month():
    """Проверяет, что возвращается пустой JSON, если год или месяц указаны неверно."""
    result = get_profitable_cashback_categories("invalid_year", "invalid_month")
    assert result == "{}"


def test_get_profitable_cashback_categories_no_transactions(sample_data_services):
    """Проверяет, что возвращается пустой JSON, если за указанный месяц нет транзакций."""
    with patch("src.services.read_excel_data", return_value=sample_data_services):
        result = get_profitable_cashback_categories("2022", "01")
        assert result == "{}"


def test_get_profitable_cashback_categories_ignore_transfers(sample_data_services):
    """Проверяет, что транзакции в категории "Переводы" игнорируются при расчете."""
    with patch("src.services.read_excel_data", return_value=sample_data_services):
        result = get_profitable_cashback_categories("2021", "12")
        result_dict = json.loads(result)
        assert "Переводы" not in result_dict


def test_get_profitable_cashback_categories_sorted(sample_data_services):
    """Проверяет, что категории сортируются по величине кэшбэка."""
    with patch("src.services.read_excel_data", return_value=sample_data_services):
        result = get_profitable_cashback_categories("2021", "12")
        result_dict = json.loads(result)
        categories = list(result_dict.keys())
        assert categories == ["Супермаркеты", "Рестораны", "Транспорт"]


def test_get_profitable_cashback_categories_json_format(sample_data_services):
    """Проверяет, что результат функции является валидным JSON"""
    with patch("src.services.read_excel_data", return_value=sample_data_services):
        result = get_profitable_cashback_categories("2021", "12")
        assert isinstance(result, str)
        try:
            json.loads(result)
        except json.JSONDecodeError:
            pytest.fail("Результат не является валидным JSON")
