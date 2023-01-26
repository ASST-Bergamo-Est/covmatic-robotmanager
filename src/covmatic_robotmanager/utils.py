import math
from functools import partial

def rad2deg(rad_list):
    return [r * 360 / (2 * math.pi) for r in rad_list]


class FunctionCase(dict):
    """ Code from covmatic-loaclwebserver project """
    def __init__(self, key):
        super(FunctionCase, self).__init__()
        self._key = key

    def case(self, key, value=None):
        if value is None:
            return partial(self.case, key)
        for k in key if isinstance(key, tuple) else (key,):
            self[k] = value
        return value

    def __call__(self, *args, **kwargs):
        try:
            return self[self._key](*args, **kwargs)
        except KeyError:
            raise NotImplementedError("No function implemented for case '{}'. Supported cases are: {}".format(self._key,
                                                                                                              ", ".join(
                                                                                                                  map("'{}'".format,
                                                                                                                      self.keys()))))


class FunctionCaseStartWith(FunctionCase):
    """ Code from covmatic-loaclwebserver project """
    def __getitem__(self, item: str):
        try:
            for k in self.keys():
                if item.startswith(k):
                    return super(FunctionCaseStartWith, self).__getitem__(k)
        except AttributeError:
            pass
        return super(FunctionCaseStartWith, self).__getitem__(item)