import re


def camel2snake(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def snake2camel(name):
    return "".join(word.title() for word in name.split("_"))
