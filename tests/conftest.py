import pytest
import pandas as pd


@pytest.fixture
def create_excel_file(tmp_path):
    file_path = tmp_path / "test_data.xlsx"
    df = pd.DataFrame({"column1": [1, 2, 3], "column2": [4, 5, 6]})
    df.to_excel(file_path, index=False)
    return file_path