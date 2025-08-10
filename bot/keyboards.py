from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

def get_style_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["Реализм", "Аниме"],
            ["Фэнтези", "Киберпанк"],
            ["Отмена"]
        ],
        one_time_keyboard=True,
        resize_keyboard=True
    )