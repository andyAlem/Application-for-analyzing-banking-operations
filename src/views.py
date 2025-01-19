import json
from datetime import datetime

import pandas as pd

from src.utils import get_common_transaction_info, read_excel_data, fetch_exchange_rates, fetch_stock_prices, greet_user, get_top_operations

def main(date_time_str):
    """
    Функция принимает дату в формате строки YYYY-MM-DD HH:MM:SS и возвращает общую информацию в формате
    json о банковских транзакциях за период с начала месяца до этой даты.
    """
    try:
        data = read_excel_data("operations.xlsx")
        data_df = pd.DataFrame(data)

        target_date = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")

        data_df["datetime"] = pd.to_datetime(data_df["Дата операции"], dayfirst=True, errors='coerce')

        start_of_month = target_date.replace(day=1)
        filtered_data = data_df[
            (data_df["datetime"] >= start_of_month) & (data_df["datetime"] <= target_date)
        ]

        filtered_data["datetime"] = filtered_data["datetime"].dt.strftime('%Y-%m-%d %H:%M:%S')


        result = {
            "greetings": greet_user(),
            "cards": get_common_transaction_info(filtered_data.to_dict(orient="records")),
            "top_transactions": get_top_operations(filtered_data.to_dict(orient="records")),
            "currency_rates": fetch_exchange_rates("user_settings.json"),
            "stock_prices": fetch_stock_prices("user_settings.json"),
        }

        return json.dumps(result, ensure_ascii=False, indent=4)

    except Exception as e:
        return json.dumps({"Ошибка": f"Ошибка при суммировании. Ошибка: {e}"}, ensure_ascii=False, indent=4)

# if __name__ == "__main__":
#     print(main(date_time_str="2020-08-11 15:25:00"))