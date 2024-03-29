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


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
