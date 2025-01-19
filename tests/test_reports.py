from unittest.mock import mock_open, patch

import pandas as pd

from src.reports import (print_name_spending_by_date, print_spending_by_date,
                         spending_by_weekday)


def test_spending_by_weekday_default_date(sample_data):
    result = spending_by_weekday(sample_data)
    assert isinstance(result, str)
    assert '"Wednesday"' in result


def test_spending_by_weekday_with_date(sample_data):
    result = spending_by_weekday(sample_data, date="2025-01-04")
    assert isinstance(result, str)
    assert '"Wednesday"' in result
    assert '"Thursday"' not in result


def test_spending_by_weekday_no_transactions(sample_data):
    sample_data_empty = sample_data.copy().iloc[0:0]
    result = spending_by_weekday(sample_data_empty)
    assert result == "{}"


def test_print_spending_by_date(sample_data):
    decorated_function = print_spending_by_date(spending_by_weekday)

    with patch("builtins.open", mock_open()) as mocked_file:
        decorated_function(sample_data)
        mocked_file.assert_called_once_with("./print_decorators/report_1.txt", "w")
        mocked_file().write.assert_called_once()


def test_print_name_spending_by_date(sample_data):
    decorated_function = print_name_spending_by_date("custom_report.txt")(spending_by_weekday)

    with patch("builtins.open", mock_open()) as mocked_file:
        decorated_function(sample_data)
        mocked_file.assert_called_once_with("./print_decorators/custom_report.txt", "w")
        mocked_file().write.assert_called_once()


def test_spending_by_weekday_error():
    invalid_data = pd.DataFrame({"Дата операции": [None], "Сумма платежа": [None]})
    result = spending_by_weekday(invalid_data)
    assert result == "{}"
