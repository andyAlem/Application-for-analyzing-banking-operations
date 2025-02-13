from unittest.mock import mock_open, patch

import pandas as pd

from src.reports import (print_name_spending_by_date, print_spending_by_date,
                         spending_by_weekday)


def test_spending_by_weekday_default_date(sample_data):
    """
    Тестирует функцию spending_by_weekday с использованием текущей даты.
    Проверяет, что результат возвращает строку, содержащую информацию о средних тратах по дням недели.
    """
    result = spending_by_weekday(sample_data)
    assert isinstance(result, str)
    assert '"Wednesday"' in result


def test_spending_by_weekday_with_date(sample_data):
    """
    Тестирует функцию spending_by_weekday с заданной датой.
    Проверяет, что результат возвращает строку с тратами, соответствующими фильтрации по дате.
    """
    result = spending_by_weekday(sample_data, date="2025-01-04")

    assert isinstance(result, str)
    assert '"Friday"' in result
    assert '"Saturday"' in result
    assert '"Sunday"' not in result


def test_spending_by_weekday_no_transactions(sample_data):
    """
    Тестирует функцию spending_by_weekday с пустыми данными.
    Проверяет, что функция возвращает пустой JSON, если в данных нет транзакций.
    """
    sample_data_empty = sample_data.copy().iloc[0:0]
    result = spending_by_weekday(sample_data_empty)
    assert result == "{}"


def test_print_spending_by_date(sample_data):
    """
    Тестирует декоратор print_spending_by_date.
    Проверяет, что результат работы функции записывается в файл с именем report.txt.
    """
    decorated_function = print_spending_by_date(spending_by_weekday)

    with patch("builtins.open", mock_open()) as mocked_file:
        decorated_function(sample_data)

        mocked_file.assert_called_once_with("./reports/report.txt", "w")

        mocked_file().write.assert_called_once()


def test_print_name_spending_by_date(sample_data):
    """
    Тестирует декоратор print_name_spending_by_date с кастомным именем файла.
    Проверяет, что результат работы функции записывается в файл с указанным именем.
    """
    decorated_function = print_name_spending_by_date(file_name="custom_report.txt")(spending_by_weekday)

    with patch("builtins.open", mock_open()) as mocked_file:
        decorated_function(sample_data)

        mocked_file.assert_called_once_with("./reports/custom_report.txt", "w")

        mocked_file().write.assert_called_once()


def test_spending_by_weekday_error():
    """
    Тестирует обработку ошибок в функции spending_by_weekday.
    Проверяет, что функция возвращает пустой JSON, если данные содержат ошибки (например, None).
    """
    invalid_data = pd.DataFrame({"Дата операции": [None], "Сумма платежа": [None]})
    result = spending_by_weekday(invalid_data)
    assert result == "{}"
