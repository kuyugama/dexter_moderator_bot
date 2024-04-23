import re
from datetime import datetime, timedelta
from typing import Union

from aiogram import types

modifiers = {
    ("г", "g"): "000000000",
    ("м", "m"): "000000",
    ("к", "k"): "000",
}
mod = {key: value for key, value in modifiers.items() for key in key}

variants = {
    "en": {
        "warnings": ("warning", "warnings", "warnings"),
        "days": ("day", "days", "days"),
        "in_days": ("day", "days", "days"),
        "months": ("month", "months", "months"),
        "in_months": ("month", "months", "months"),
        "years": ("year", "years", "years"),
        "in_years": ("year", "years", "years"),
        "weeks": ("week", "weeks", "weeks"),
        "in_weeks": ("week", "weeks", "weeks"),
        "minutes": ("minute", "minutes", "minutes"),
        "in_minutes": ("minute", "minutes", "minutes"),
        "seconds": ("second", "seconds", "seconds"),
        "in_seconds": ("second", "seconds", "seconds"),
        "hours": ("hour", "hours", "hours"),
        "in_hours": ("hour", "hours", "hours"),
        "units": ("unit", "units", "units"),
        "in_units": ("unit", "units", "units"),
        "__sep": " and ",
    },
    "uk": {
        "warnings": ("попередження", "попередження", "попереджень"),
        "days": ("день", "дня", "днів"),
        "in_days": ("день", "дня", "днів"),
        "months": ("місяць", "місяці", "місяців"),
        "in_months": ("місяць", "місяці", "місяців"),
        "years": ("рік", "роки", "років"),
        "in_years": ("рік", "роки", "років"),
        "weeks": ("тиждень", "тижні", "тижнів"),
        "in_weeks": ("тиждень", "тижні", "тижнів"),
        "minutes": ("хвилина", "хвилини", "хвилин"),
        "in_minutes": ("хвилину", "хвилини", "хвилин"),
        "seconds": ("секунда", "секунди", "секунд"),
        "in_seconds": ("секунду", "секунди", "секунд"),
        "hours": ("година", "години", "годин"),
        "in_hours": ("годину", "години", "годин"),
        "units": ("одиниця", "одиниці", "одиниць"),
        "in_units": ("одиницю", "одиниці", "одиниць"),
        "__sep": " і ",
    },
}


def get_mention(user: types.User | types.Chat) -> str:
    if isinstance(user, types.Chat):
        return user.title
    user_mention = user.mention_html()

    if user.username:
        user_mention += f"(@{user.username}|id<code>{user.id}</code>)"
    else:
        user_mention += f"(id<code>{user.id}</code>)"

    return user_mention


mention_regex = re.compile(r"(id\d+|@\w+)")


def extract_user_mention(string: str) -> tuple[str | int, str] | None:
    match = mention_regex.search(string)
    if not match:
        return None
    mention = match.group(0)
    if not mention:
        return None
    if mention.startswith("id"):
        mention = int(mention[2:])
    else:
        mention = mention[1:]

    return mention, " ".join(
        word for word in mention_regex.sub("", string).split(" ") if word != ""
    )


def beautify_number(number: Union[str, int, float]) -> str:
    if isinstance(number, int):
        number = str(number)
    elif isinstance(number, float):
        number, floating = str(number).split(".")
        return f"{beautify_number(number)}.{floating}"

    result = "".join(
        [
            f"{char} " if index % 3 == 0 else char
            for index, char in enumerate(number[::-1], 1)
        ]
    )[::-1].strip()

    if len(result) > 1 and result[0] in "-+" and result[1] == " ":
        result = result.replace(" ", "", 1)

    return result


def to_int(value: Union[float, str, int]) -> Union[int, str]:
    if isinstance(value, int):
        return value
    elif isinstance(value, float):
        return int(value)
    elif not isinstance(value, str):
        raise ValueError(f"Cannot handle value type {value.__class__}")

    if not len(value):
        return "nan"

    value = value.replace(" ", "")

    integer = "".join([char if char not in mod else mod[char] for char in value])

    if "." in integer:
        integer = to_float(integer)
        if integer == "nan":
            return "nan"
        integer = int(integer)

    if all(list(map(lambda x: x in mod, value))):
        integer = "1" + integer
    return (
        int(integer)
        if (
            isinstance(integer, int)
            or integer.isdigit()
            or integer.startswith("-")
            and integer[1:].isdigit()
        )
        else "nan"
    )


def to_float(value: str) -> Union[float, str]:
    if isinstance(value, float):
        return value
    elif isinstance(value, int):
        return float(value)
    elif not isinstance(value, str):
        raise ValueError(f"Cannot handle value type {value.__class__}")

    if value.count(".") != 1:
        return "nan"

    value = value.replace(" ", "")

    num, floating = value.split(".")

    if len(floating) == 0:
        floating = "0"
    elif len(num) == 0:
        num = "0"

    if floating.endswith("0") and len(floating) > 1:
        floating = floating.rstrip("0")

    if floating.startswith("0") and len(floating) > 1:
        count_of_zeros = 0
        for char in floating:
            if char != "0":
                break
            count_of_zeros += 1

        floating = "0" * count_of_zeros + str(to_int(floating[count_of_zeros:]))
        if "nan" in floating:
            return "nan"

    if num.startswith("0"):
        num = num.strip("0")

    if "nan" == to_int(num):
        return "nan"

    return float(num + "." + floating)


def beautify_represent(
    number: int, translate: str = "days", language="en", number_formatter_func=None
):
    if (number := to_int(number)) == "nan":
        return "unrecognizable value"

    local_variants = variants[language]

    units = abs(number) % 10

    if abs(number) % 100 // 10 == 1:
        result = local_variants[translate][2]
    elif units == 0 or units > 4:
        result = local_variants[translate][2]
    elif units > 1:
        result = local_variants[translate][1]
    else:
        result = local_variants[translate][0]

    if translate not in (
        "days",
        "months",
        "weeks",
        "years",
        "years",
        "seconds",
        "minutes",
        "hours",
        "in_days",
        "in_months",
        "in_weeks",
        "in_years",
        "in_years",
        "in_seconds",
        "in_minutes",
        "in_hours",
    ):
        if number_formatter_func:
            return f"{number_formatter_func(number)} {result}"

        return result

    if number_formatter_func:
        return f"{number_formatter_func(number)} {result}"

    return f"{number} {result}"


def beautify_time(
    time: Union[int, str, timedelta, datetime] = None,
    _in=False,
    language="en",
    days: int = None,
    hours: int = None,
    minutes: int = None,
    seconds: int = None,
) -> str:
    if time is None and (
        days is None and hours is None and minutes and None and seconds is None
    ):
        raise ValueError(
            "If you don't put the argument time you must put "
            "one or more arguments of days/hours/minutes/seconds"
        )

    if time is None:
        if not days:
            days = 0

        if not hours:
            hours = 0

        if not minutes:
            minutes = 0

        if not seconds:
            seconds = 0

    if isinstance(time, timedelta):
        time = str(time)
    elif isinstance(time, datetime):
        time = time.strftime("%H:%M:%S")
    elif isinstance(time, int):
        time = str(timedelta(seconds=time))
    elif time is not None and not isinstance(time, str):
        return "unrecognized.."

    if time is not None:
        words = time.split(" ")
        words_count = len(words)
        days = 0
        if words_count == 3 and words[1].startswith("day"):
            days = to_int(words[0])
            if days == "nan":
                days = 0

        # hours, minutes and seconds
        hms = words[-1]
        if "." in hms:
            hms = hms.split(".", maxsplit=1)[0]

        hours, minutes, seconds = map(int, hms.split(":"))

    if seconds // 60:
        minutes = seconds // 60
        seconds %= 60

    if minutes // 60:
        hours = minutes // 60
        minutes %= 60

    if hours // 24:
        days = hours // 24
        hours %= 24

    numerate = ("years", "months", "weeks", "days", "hours", "minutes", "seconds")
    if _in:
        numerate = (
            "in_years",
            "in_months",
            "in_weeks",
            "in_days",
            "in_hours",
            "in_minutes",
            "in_seconds",
        )

    result = []

    if days // 365:
        result.append(beautify_represent(days // 365, numerate[0], language=language))
        days %= 365

    if days // 31:
        result.append(beautify_represent(days // 31, numerate[1], language=language))
        days %= 31

    if days // 7:
        result.append(beautify_represent(days // 7, numerate[2], language=language))
        days %= 7

    if days:
        result.append(beautify_represent(days, numerate[3], language=language))

    if hours:
        result.append(beautify_represent(hours, numerate[4], language=language))

    if minutes:
        result.append(beautify_represent(minutes, numerate[5], language=language))

    if seconds:
        result.append(beautify_represent(seconds, numerate[6], language=language))

    if len(result) == 1:
        return result[0]
    elif len(result) == 0:
        return beautify_represent(0, "seconds", language=language)

    return ", ".join(result[:-1]) + variants[language]["__sep"] + result[-1]


variables_regex = re.compile(
    r"([\w\d.]+)\s*[:=]\s*(null|nil|infinity|да|нет|true|false|'.*'|\".*\"|[-\dкмkm]+)",
    flags=re.IGNORECASE,
)


def parse_variables(string: str) -> dict:
    raw_variables = variables_regex.findall(string)
    variables = {}
    for name, value in raw_variables:
        if to_int(value) != "nan":
            value = to_int(value)
        elif value in ("true", "да"):
            value = True
        elif value in ("false", "нет"):
            value = False
        elif value.startswith("'"):
            value = value.strip("'")
        elif value.startswith('"'):
            value = value.strip('"')
        elif value == "infinity":
            value = float("inf")
        else:
            value = None
        variables[name] = value
    return variables


def from_int(num):
    if isinstance(num, int):
        num = str(num)
    elif not isinstance(num, str):
        return

    if len(num) < 1:
        return

    result = num[0]

    past_of_number = ""
    modificators = ""
    for index, char in enumerate(num[:0:-1], start=1):
        past_of_number += char
        if index % 3 == 0:
            modificators += "k"
            past_of_number = ""

    if len(num[len(past_of_number) + 1 :]):
        additional_number = num[len(past_of_number) + 1 :][0]

        if additional_number != "0":
            past_of_number += "," + additional_number
    result += past_of_number + modificators.replace("kkk", "g").replace("kk", "m")

    return result


def slicer(s, length):
    for index in range(0, len(s), length):
        yield s[index : index + length]


def wordwrap(text: str, limit: int = 20):
    if len(text) <= limit:
        return text
    lines = text.splitlines()

    result = []
    temporary_line = ""

    for line in lines:
        if len(line) < limit:
            result += [line]
            continue

        for word in line.split(" "):
            if word == "":
                word = " "
            if len(word) > limit:
                if len(temporary_line):
                    result.append(temporary_line[:-1])
                    temporary_line = ""
                result.append("\n".join(slicer(word, limit)))
                continue
            if not word.endswith(" "):
                word += " "
            if len(temporary_line + word) > limit:
                result.append(temporary_line[:-1])
                temporary_line = word
            else:
                temporary_line += word

        if temporary_line != "":
            result.append(temporary_line[:-1])
            temporary_line = ""

    return "\n".join(result)
