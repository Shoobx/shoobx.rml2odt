###############################################################################
#
# Copyright 2013-2016 by Shoobx, Inc.
#
###############################################################################
"""Number to Words Formatter
"""
from __future__ import absolute_import

import math
import six


class Number2Words(object):

    units = [
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen",
        ]

    units_ordinal = [
        "zeroth", "first", "second", "third", "fourth", "fifth", "sixth",
        "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth",
        "thirteenth", "fourteenth", "fifteenth", "sixteenth", "seventeenth",
        "eighteenth", "nineteenth",
        ]

    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
            "eighty", "ninety"]

    tens_ordinal = ["", "", "twentieth", "thirtieth", "fortieth", "fiftieth",
                    "sixtieth", "seventieth", "eightieth", "ninetieth"]

    scales = ["", "", "hundred", "thousand", "", "", "million", "", "",
              "billion", "", "", "trillion"]

    def fmtTextNumber(self, num, unit_text=None, unit_symbol=None,
                      ordinal=False):
        negative = False
        if int(num) < 0:
            negative = True
        output = self(abs(int(num)), ordinal=ordinal)
        if negative:
            output = "negative " + output
        if unit_text is not None and unit_symbol is not None:
            output += u' ' + unit_text
        output += u' (' + self.fmtNumber(num, ordinal=ordinal)
        if unit_symbol is not None:
            output += unit_symbol
        output += u')'
        if unit_text is not None and unit_symbol is None:
            output += u' ' + unit_text
        return output

    def fmtNumber(self, num, ordinal=False):
        str_num = six.text_type(num)
        if ordinal:
            str_num += "tsnrhtdd"[
                (num / 10 % 10 != 1) * (num % 10 < 4) * num % 10::4]
        return str_num

    def __call__(self, num, as_list=False, ordinal=False):
        num_str = str(num)
        num_left = num_str
        words = []
        while num_left:
            if int(num_left) < 20:
                if int(num_left) != 0 or not len(words):
                    words.append(self.units[int(num_left)])
                break
            if int(num_left) < 100:
                words.append(self.tens[int(num_left[0])])
                num_left = num_left[1:]
            elif int(num_left) < 1000:
                scale = self.scales[len(num_left)-1]
                digit = int(num_left[0])
                if digit != 0:
                    words.append(self.units[digit])
                words.append(scale)
                num_left = num_left[1:]
            else:
                mag = int(math.log10(int(num_left))/3)*3
                words += self(num_left[:-mag], True) + [self.scales[mag]]
                num_left = num_left[-mag:]

        if ordinal:
            if words[-1] in self.units:
                words[-1] = self.units_ordinal[self.units.index(words[-1])]
            elif words[-1] in self.tens:
                words[-1] = self.tens_ordinal[self.tens.index(words[-1])]
            elif words[-1] in self.scales:
                words[-1] += 'th'
        words = [w.title() for w in words if w != '']
        if as_list:
            return words
        if len(words) > 1 and (
                words[-2] in [w.title() for w in self.tens] and
                words[-1] in [w.title() for w in self.units +
                              self.units_ordinal]):
            ten_ones = u'-'.join(words[-2:])
            words = words[:-2]
            words.append(ten_ones)
        return u' '.join(words)
