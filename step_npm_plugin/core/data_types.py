

class SecureString:
    """
    Special datatype that will only output its value when you explicitly call `to_string()`.

    This is to prevent accidentally blind dumping sensitive data in to logs.
    """
    _value: str = None

    def __init__(self, string: str):
        self._value = string

    def to_string(self):
        return self._value

    def __str__(self):
        return "*" * 10

    def __repr__(self):
        return self.__str__()
