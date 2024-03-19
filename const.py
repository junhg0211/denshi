from json import load


with open("secret.json", "r", encoding="utf-8") as file:
    _secret = load(file)


def _get(dict_, path):
    result = dict_

    for directory in path.split():
        result = result.get(directory)

        if result is None:
            return None

    return result


def get_secret(path):
    return _get(_secret, path)
