import json
import logging
from src.utils import greeting_by_time_of_day, filter_by_date, reading_excel_file, card_expenses
from src.utils import transaction_rating_by_amount, exchange_rate, get_price_stock, date_now, get_user_settings



logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(filename)s - %(levelname)s - %(message)s",
    filename="../logs/views.log",
    filemode="w",
)

main_logger = logging.getLogger()


def load_data():
    try:
        my_list = reading_excel_file("../data/operations.xlsx")
        user_settings = get_user_settings("../data/user_settings.json")
        stocks = user_settings["user_stocks"]
        currency = user_settings["user_currencies"]
        return my_list, stocks, currency
    except Exception as e:
        main_logger.error(f"Ошибка при загрузке данных: {e}")
        return [], {}, {}


def create_json_response(greeting, cards, top_trans, currency_r, stocks_prices):
    result = [{
        "greeting": greeting,
        "cards": cards,
        "top_transactions": top_trans,
        "currency_rates": currency_r,
        "stock_prices": stocks_prices,
    }]
    return json.dumps(result, indent=4, ensure_ascii=False)


def main(user_data: str) -> str:
    main_logger.info('Начало работы функции main')

    my_list, stocks, currency = load_data()
    if not my_list or not stocks or not currency:
        main_logger.error("Не удалось загрузить все необходимые данные")
        return json.dumps({"error": "Не удалось загрузить данные"})

    final_list = filter_by_date(user_data, my_list)
    greeting = greeting_by_time_of_day(date_now)
    cards = card_expenses(final_list)
    top_trans = transaction_rating_by_amount(final_list)
    stocks_prices = get_price_stock(stocks)
    currency_r = exchange_rate(currency)

    main_logger.info('Формирование JSON ответа')
    # Формирование и возврат ответа
    date_json = create_json_response(greeting, cards, top_trans, currency_r, stocks_prices)

    main_logger.info("Завершение работы функции main")
    return date_json


# Пример вызова
print(main('2021-10-20'))