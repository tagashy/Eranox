from typing import Union, List


def has_parameter(parameter: Union[str, List[str]], kwargs: dict):
    if isinstance(parameter, str):
        if parameter in kwargs:
            return True
        else:
            return False
    elif isinstance(parameter, list):
        for param in parameter:
            if not has_parameter(param, kwargs):
                return False
        else:
            return True
    else:
        raise NotImplementedError()