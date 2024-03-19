from os.path import isfile
from json import load, dump


if not isfile("database.json"):
    unit = input("돈의 단위를 입력해주세요: ")
    data = {"currency": {"unit": unit}, "users": {}}
    with open("database.json", "w", encoding="utf-8") as file:
        dump(data, file, ensure_ascii=False, indent=2)


def _load_data() -> dict:
    with open("database.json", "r", encoding="utf-8") as file:
        return load(file)


def _save_data(data: dict):
    with open("database.json", "w", encoding="utf-8") as file:
        dump(data, file, ensure_ascii=False, indent=2)


def get_unit() -> str:
    data = _load_data()
    return data["currency"]["unit"]


def get_money(user_id: int) -> int:
    data = _load_data()

    user_data = data["users"].get(str(user_id), None)
    if user_data is None:
        user_data = {"money": 0}
        data["users"][str(user_id)] = user_data
        _save_data(data)
        return 0

    money = user_data.get("money", 0)
    return money


def set_money(user_id: int, money: int):
    data = _load_data()

    user_data = data["users"].get(str(user_id), None)
    if user_data is None:
        user_data = {"money": money}
        data["users"][str(user_id)] = user_data
    else:
        data["users"][str(user_id)]["money"] = money

    return _save_data(data)
