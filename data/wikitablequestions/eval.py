# SPDX-License-Identifier: CC-BY-SA-4.0
"""WikiTableQuestions denotation grading for Benchopedia sweeps.

The value classes and normalization are adapted from the official evaluator
at 7d455a5a707b96341ef72aff9428749d443d8aa9. The tagged reference values use
the pristine-unseen-tables split from that commit. See redistribution-review.md.
"""

from abc import ABCMeta, abstractmethod
from math import isinf, isnan
import re
import unicodedata

ATTEMPTS = 2
INSTRUCTION = "Return only the answer values, one per line, with no numbering or explanation."


def messages(task):
    return [{"role": "user", "content": f"{task['prompt']}\n\n{INSTRUCTION}"}]


def grade(task, output):
    values = [line.strip() for line in output.split("\n") if line.strip()]
    if not values:
        return "unparseable", None
    target = to_value_list(task["solution"].split("\n"), TAGGED_VALUES.get(task["key"]))
    predicted = to_value_list(values)
    return ("pass" if check_denotation(target, predicted) else "fail"), "\n".join(values)


# Python 3 port of the authors' normalization and denotation comparison.
def normalize(x):
    if not isinstance(x, str):
        x = x.decode('utf8', errors='ignore')
    # Remove diacritics
    x = ''.join(c for c in unicodedata.normalize('NFKD', x)
                if unicodedata.category(c) != 'Mn')
    # Normalize quotes and dashes
    x = re.sub(r"[‘’´`]", "'", x)
    x = re.sub(r"[“”]", "\"", x)
    x = re.sub(r"[‐‑‒–—−]", "-", x)
    while True:
        old_x = x
        # Remove citations
        x = re.sub(r"((?<!^)\[[^\]]*\]|\[\d+\]|[•♦†‡*#+])*$", "", x.strip())
        # Remove details in parenthesis
        x = re.sub(r"(?<!^)( \([^)]*\))*$", "", x.strip())
        # Remove outermost quotation mark
        x = re.sub(r'^"([^"]*)"$', r'\1', x.strip())
        if x == old_x:
            break
    # Remove final '.'
    if x and x[-1] == '.':
        x = x[:-1]
    # Collapse whitespaces and convert to lower case
    x = re.sub(r'\s+', ' ', x, flags=re.U).lower().strip()
    return x


class Value(object, metaclass=ABCMeta):
    _normalized = None

    @abstractmethod
    def match(self, other):
        """Return True if the value matches the other value.

        Args:
            other (Value)
        Returns:
            a boolean
        """
        pass

    @property
    def normalized(self):
        return self._normalized


class StringValue(Value):

    def __init__(self, content):
        assert isinstance(content, str)
        self._normalized = normalize(content)
        self._hash = hash(self._normalized)

    def __eq__(self, other):
        return isinstance(other, StringValue) and self.normalized == other.normalized

    def __hash__(self):
        return self._hash

    def __str__(self):
        return 'S' +  str([self.normalized])
    __repr__ = __str__

    def match(self, other):
        assert isinstance(other, Value)
        return self.normalized == other.normalized


class NumberValue(Value):

    def __init__(self, amount, original_string=None):
        assert isinstance(amount, (int, float))
        if abs(amount - round(amount)) < 1e-6:
            self._amount = int(amount)
        else:
            self._amount = float(amount)
        if not original_string:
            self._normalized = str(self._amount)
        else:
            self._normalized = normalize(original_string)
        self._hash = hash(self._amount)

    @property
    def amount(self):
        return self._amount

    def __eq__(self, other):
        return isinstance(other, NumberValue) and self.amount == other.amount

    def __hash__(self):
        return self._hash

    def __str__(self):
        return ('N(%f)' % self.amount) + str([self.normalized])
    __repr__ = __str__

    def match(self, other):
        assert isinstance(other, Value)
        if self.normalized == other.normalized:
            return True
        if isinstance(other, NumberValue):
            return abs(self.amount - other.amount) < 1e-6
        return False

    @staticmethod
    def parse(text):
        """Try to parse into a number.

        Return:
            the number (int or float) if successful; otherwise None.
        """
        try:
            if "_" in text:
                return None
            return int(text)
        except:
            try:
                amount = float(text)
                assert not isnan(amount) and not isinf(amount)
                return amount
            except:
                return None


class DateValue(Value):

    def __init__(self, year, month, day, original_string=None):
        """Create a new DateValue. Placeholders are marked as -1."""
        assert isinstance(year, int)
        assert isinstance(month, int) and (month == -1 or 1 <= month <= 12)
        assert isinstance(day, int) and (day == -1 or 1 <= day <= 31)
        assert not (year == month == day == -1)
        self._year = year
        self._month = month
        self._day = day
        if not original_string:
            self._normalized = '{}-{}-{}'.format(
                year if year != -1 else 'xx',
                month if month != -1 else 'xx',
                day if day != '-1' else 'xx')
        else:
            self._normalized = normalize(original_string)
        self._hash = hash((self._year, self._month, self._day))

    @property
    def ymd(self):
        return (self._year, self._month, self._day)

    def __eq__(self, other):
        return isinstance(other, DateValue) and self.ymd == other.ymd

    def __hash__(self):
        return self._hash

    def __str__(self):
        return (('D(%d,%d,%d)' % (self._year, self._month, self._day))
                + str([self._normalized]))
    __repr__ = __str__

    def match(self, other):
        assert isinstance(other, Value)
        if self.normalized == other.normalized:
            return True
        if isinstance(other, DateValue):
            return self.ymd == other.ymd
        return False

    @staticmethod
    def parse(text):
        """Try to parse into a date.

        Return:
            tuple (year, month, date) if successful; otherwise None.
        """
        try:
            if "_" in text:
                return None
            ymd = text.lower().split('-')
            assert len(ymd) == 3
            year = -1 if ymd[0] in ('xx', 'xxxx') else int(ymd[0])
            month = -1 if ymd[1] == 'xx' else int(ymd[1])
            day = -1 if ymd[2] == 'xx' else int(ymd[2])
            assert not (year == month == day == -1)
            assert month == -1 or 1 <= month <= 12
            assert day == -1 or 1 <= day <= 31
            return (year, month, day)
        except:
            return None


def to_value(original_string, corenlp_value=None):
    """Convert the string to Value object.

    Args:
        original_string (basestring): Original string
        corenlp_value (basestring): Optional value returned from CoreNLP
    Returns:
        Value
    """
    if isinstance(original_string, Value):
        # Already a Value
        return original_string
    if not corenlp_value:
        corenlp_value = original_string
    # Number?
    amount = NumberValue.parse(corenlp_value)
    if amount is not None:
        return NumberValue(amount, original_string)
    # Date?
    ymd = DateValue.parse(corenlp_value)
    if ymd is not None:
        if ymd[1] == ymd[2] == -1:
            return NumberValue(ymd[0], original_string)
        else:
            return DateValue(ymd[0], ymd[1], ymd[2], original_string)
    # String.
    return StringValue(original_string)


def to_value_list(original_strings, corenlp_values=None):
    """Convert a list of strings to a list of Values

    Args:
        original_strings (list[basestring])
        corenlp_values (list[basestring or None])
    Returns:
        list[Value]
    """
    assert isinstance(original_strings, (list, tuple, set))
    if corenlp_values is not None:
        assert isinstance(corenlp_values, (list, tuple, set))
        assert len(original_strings) == len(corenlp_values)
        return list(set(to_value(x, y) for (x, y)
                in zip(original_strings, corenlp_values)))
    else:
        return list(set(to_value(x) for x in original_strings))


def check_denotation(target_values, predicted_values):
    """Return True if the predicted denotation is correct.

    Args:
        target_values (list[Value])
        predicted_values (list[Value])
    Returns:
        bool
    """
    # Check size
    if len(target_values) != len(predicted_values):
        return False
    # Check items
    for target in target_values:
        if not any(target.match(pred) for pred in predicted_values):
            return False
    return True


# Values whose CoreNLP annotation changes their type or value.
TAGGED_VALUES = {
    'nu-1': ['100000.0'],
    'nu-2': ['17.0'],
    'nu-3': ['1995-01-26'],
    'nu-19': ['492111.0'],
    'nu-45': ['504000.0'],
    'nu-56': ['460252.0'],
    'nu-66': ['2010-12-06'],
    'nu-96': ['1560000000.0'],
    'nu-97': ['2011-10-xx'],
    'nu-104': ['6.0'],
    'nu-118': ['xxxx-10-17'],
    'nu-128': ['2005-08-27'],
    'nu-142': ['2005-06-14'],
    'nu-153': ['48.4', '22.52', '25.29', '3.79'],
    'nu-183': ['76000.0'],
    'nu-194': ['2.0'],
    'nu-223': ['142000.0'],
    'nu-229': ['4.0'],
    'nu-259': ['5.0'],
    'nu-299': ['1998-06-28'],
    'nu-312': ['xxxx-12-21'],
    'nu-333': ['202.6'],
    'nu-365': ['1.0'],
    'nu-366': ['132.0'],
    'nu-394': ['202.0'],
    'nu-425': ['183.0'],
    'nu-439': ['2013-02-01'],
    'nu-443': ['1987-11-25'],
    'nu-448': ['352000.0'],
    'nu-449': ['415.0'],
    'nu-476': ['1.0'],
    'nu-482': ['xxxx-08-31'],
    'nu-491': ['21840.0'],
    'nu-492': ['2000.0'],
    'nu-515': ['2008-12-27'],
    'nu-517': ['1920-10-16'],
    'nu-530': ['62176.0'],
    'nu-535': ['64345.0'],
    'nu-538': ['1950.0'],
    'nu-565': ['220000.0'],
    'nu-570': ['7.0'],
    'nu-575': ['209945.0'],
    'nu-589': ['2008-10-31'],
    'nu-616': ['10.0'],
    'nu-624': ['80.0'],
    'nu-639': ['132046.0'],
    'nu-644': ['xxxx-11-05'],
    'nu-648': ['2009-11-01'],
    'nu-668': ['xxxx-10-23'],
    'nu-670': ['12000000000.0'],
    'nu-671': ['1.0'],
    'nu-685': ['0.9'],
    'nu-689': ['1964-03-21', 'Denver'],
    'nu-695': ['8.0'],
    'nu-716': ['4.6'],
    'nu-749': ['4220.0', '13845.0'],
    'nu-788': ['3.0'],
    'nu-822': ['2007-07-25'],
    'nu-848': ['17259.0'],
    'nu-860': ['1.0'],
    'nu-865': ['xxxx-09-xx'],
    'nu-881': ['28061313.0'],
    'nu-896': ['63.5'],
    'nu-914': ['xxxx-10-xx'],
    'nu-953': ['1998-09-20'],
    'nu-969': ['1.0'],
    'nu-975': ['1999-11-06'],
    'nu-1005': ['1514069.0'],
    'nu-1009': ['4.0'],
    'nu-1010': ['1992-08-29'],
    'nu-1024': ['13.0'],
    'nu-1046': ['1.0'],
    'nu-1067': ['2.0'],
    'nu-1069': ['xxxx-12-xx'],
    'nu-1087': ['47900.0'],
    'nu-1103': ['1500.0'],
    'nu-1116': ['2009-11-01'],
    'nu-1132': ['xxxx-09-xx', 'xxxx-10-xx'],
    'nu-1171': ['2013-07-11'],
    'nu-1173': ['2010-05-16'],
    'nu-1202': ['2.0'],
    'nu-1203': ['75287.0'],
    'nu-1208': ['2.0'],
    'nu-1215': ['1.0'],
    'nu-1221': ['1960-08-31'],
    'nu-1230': ['54.0'],
    'nu-1238': ['2.0'],
    'nu-1246': ['9563.0'],
    'nu-1256': ['1.0'],
    'nu-1260': ['2011-02-13'],
    'nu-1267': ['1995-01-02'],
    'nu-1281': ['23.0'],
    'nu-1285': ['13129.0'],
    'nu-1286': ['xxxx-02-16'],
    'nu-1302': ['2009-12-24'],
    'nu-1414': ['27.0'],
    'nu-1422': ['6.0'],
    'nu-1424': ['2001-09-23'],
    'nu-1435': ['588865.0'],
    'nu-1449': ['2069-05-20'],
    'nu-1472': ['9.0'],
    'nu-1475': ['2.0'],
    'nu-1508': ['1795-02-xx'],
    'nu-1544': ['34700000000.0'],
    'nu-1591': ['24860000.0'],
    'nu-1621': ['1944-09-13'],
    'nu-1640': ['1985-12-15'],
    'nu-1645': ['6272571.0'],
    'nu-1648': ['2069-05-20'],
    'nu-1655': ['1981-10-11'],
    'nu-1689': ['17.0'],
    'nu-1710': ['5.0'],
    'nu-1711': ['54500.0'],
    'nu-1745': ['2006-04-14'],
    'nu-1791': ['1997-09-20'],
    'nu-1822': ['100.0'],
    'nu-1830': ['0.9'],
    'nu-1860': ['28.0'],
    'nu-1868': ['14.0'],
    'nu-1882': ['47900.0'],
    'nu-1887': ['172000.0'],
    'nu-1946': ['13659.0'],
    'nu-1958': ['xxxx-11-10'],
    'nu-1971': ['1.15'],
    'nu-2010': ['27426028.0'],
    'nu-2063': ['1992-08-15', '1992-08-19', '1993-04-07', '1993-04-13'],
    'nu-2078': ['1983-11-13'],
    'nu-2090': ['2013-05-16'],
    'nu-2091': ['xxxx-07-29'],
    'nu-2094': ['29133000.0'],
    'nu-2118': ['1.0'],
    'nu-2122': ['2227000.0'],
    'nu-2138': ['6.0'],
    'nu-2147': ['106.3'],
    'nu-2226': ['98453.0'],
    'nu-2231': ['202.6'],
    'nu-2242': ['2007-11-11'],
    'nu-2278': ['xxxx-08-08'],
    'nu-2298': ['2013-07-11'],
    'nu-2380': ['2013-02-09'],
    'nu-2384': ['4.0'],
    'nu-2395': ['2003-12-09'],
    'nu-2408': ['0.366'],
    'nu-2413': ['2004.0', '2008.0', '2012.0'],
    'nu-2435': ['1961-04-22'],
    'nu-2455': ['1982-10-16'],
    'nu-2461': ['1994-12-11'],
    'nu-2477': ['60.45'],
    'nu-2504': ['8.0'],
    'nu-2543': ['xxxx-10-18'],
    'nu-2549': ['3.0'],
    'nu-2559': ['14.0'],
    'nu-2560': ['1931-10-03'],
    'nu-2564': ['4.0'],
    'nu-2585': ['1972-11-11'],
    'nu-2591': ['1624.0'],
    'nu-2605': ['2.0'],
    'nu-2626': ['1987-09-27'],
    'nu-2631': ['xxxx-02-16'],
    'nu-2644': ['1961-04-29'],
    'nu-2648': ['1795-02-xx'],
    'nu-2651': ['18690.0'],
    'nu-2652': ['xxxx-09-11'],
    'nu-2655': ['4.0'],
    'nu-2664': ['21.0'],
    'nu-2693': ['4954.0'],
    'nu-2716': ['26.0'],
    'nu-2748': ['21.16'],
    'nu-2758': ['2008-05-10'],
    'nu-2801': ['1918-07-11'],
    'nu-2807': ['93505.0'],
    'nu-2811': ['7.0'],
    'nu-2815': ['2003-01-25'],
    'nu-2827': ['7.0'],
    'nu-2834': ['2.0'],
    'nu-2839': ['2013-05-19'],
    'nu-2864': ['2.0'],
    'nu-2868': ['2.0'],
    'nu-2881': ['59.51', '17.76', '62.86', '63.5', '62.58', '18.44', '60.99', '57.79', '56.98'],
    'nu-2896': ['0.13'],
    'nu-2917': ['1094000.0'],
    'nu-2932': ['8.0'],
    'nu-2972': ['1.0'],
    'nu-2989': ['1146000.0'],
    'nu-2992': ['5.0'],
    'nu-2996': ['143.0'],
    'nu-3008': ['13129.0'],
    'nu-3024': ['2.0'],
    'nu-3059': ['2000-10-06'],
    'nu-3095': ['15.0'],
    'nu-3097': ['557000.0'],
    'nu-3107': ['xxxx-09-12'],
    'nu-3131': ['1994-11-01'],
    'nu-3191': ['31.0'],
    'nu-3207': ['5.0'],
    'nu-3212': ['1952-01-25'],
    'nu-3245': ['7.0'],
    'nu-3285': ['1972-11-11'],
    'nu-3292': ['1944-03-08'],
    'nu-3342': ['3.0'],
    'nu-3366': ['100000.0'],
    'nu-3373': ['1200000000.0'],
    'nu-3392': ['xxxx-02-01'],
    'nu-3398': ['2009-11-01'],
    'nu-3402': ['3345248.0'],
    'nu-3407': ['xxxx-10-13'],
    'nu-3408': ['3.0'],
    'nu-3409': ['2013-01-01', '4:10 PM'],
    'nu-3440': ['34.0'],
    'nu-3474': ['858209.0'],
    'nu-3478': ['13.0'],
    'nu-3496': ['12000.0'],
    'nu-3516': ['6.0'],
    'nu-3564': ['200227.0'],
    'nu-3567': ['1470.0'],
    'nu-3569': ['2013-01-19'],
    'nu-3577': ['10.0'],
    'nu-3599': ['74871.0'],
    'nu-3606': ['5.0'],
    'nu-3631': ['32100.0'],
    'nu-3640': ['473000.0'],
    'nu-3649': ['8.0'],
    'nu-3664': ['5.0'],
    'nu-3711': ['83.0'],
    'nu-3745': ['1960-10-29'],
    'nu-3766': ['2009-05-23'],
    'nu-3779': ['2008-06-04'],
    'nu-3785': ['1982-06-13'],
    'nu-3821': ['13.0'],
    'nu-3825': ['11630000.0'],
    'nu-3838': ['2006-03-04'],
    'nu-3855': ['50.0'],
    'nu-3896': ['1994-10-15'],
    'nu-3913': ['2007-12-17'],
    'nu-3932': ['56.98'],
    'nu-3936': ['14.0'],
    'nu-3951': ['xxxx-09-29'],
    'nu-3965': ['119.0'],
    'nu-3966': ['5.0'],
    'nu-3974': ['19.5'],
    'nu-3986': ['11.0'],
    'nu-4013': ['2.0'],
    'nu-4099': ['1986-12-14'],
    'nu-4102': ['2011-02-13'],
    'nu-4103': ['1938-11-11'],
    'nu-4126': ['1992-12-12'],
    'nu-4149': ['7.0'],
    'nu-4188': ['1.0'],
    'nu-4212': ['48211.0'],
    'nu-4213': ['4.0'],
    'nu-4214': ['12.0'],
    'nu-4244': ['1918-07-11'],
    'nu-4255': ['2012-12-xx'],
    'nu-4256': ['4.0'],
    'nu-4289': ['xxxx-10-24'],
    'nu-4298': ['2.0'],
    'nu-4301': ['2.0'],
    'nu-4324': ['2016-03-09'],
    'nu-4325': ['60.28'],
}
