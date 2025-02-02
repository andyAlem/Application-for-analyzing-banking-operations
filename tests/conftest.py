import pandas as pd
import pytest


@pytest.fixture
def create_excel_file(tmp_path):
    file_path = tmp_path / "test_data.xlsx"
    df = pd.DataFrame({"column1": [1, 2, 3], "column2": [4, 5, 6]})
    df.to_excel(file_path, index=False)
    return file_path


@pytest.fixture
def sample_data():
    """
    Фикстура для предоставления тестовых данных.
    """
    data = {
        "Дата операции": ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04", "2025-01-05"],
        "Сумма платежа": [100, 200, 150, 50, 300],
    }
    return pd.DataFrame(data)
