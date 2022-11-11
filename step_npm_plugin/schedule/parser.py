

NOTATIONS = {
    'd': 86400,
    'h': 3600,
    'm': 60,
    's': 1
}


MAX_WAIT = 86400


def parse_time(time_string: str):
    notation = time_string[-1]

    if notation not in NOTATIONS.keys():
        raise ValueError(f'Invalid time notation provided. Only support: {NOTATIONS.keys()}')

    try:
        units = int(time_string[:-1])
    except TypeError:
        raise TypeError('Invalid time format provided. Must be a whole number with a single char on the end.')

    seconds = units * NOTATIONS[notation.lower()]

    if seconds > MAX_WAIT:
        raise ValueError(f'Maximum wait time is {MAX_WAIT} seconds.')

    return seconds
