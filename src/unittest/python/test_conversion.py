import pytest
import sys
import unittest


from src.main.python.conversion import Conversion
from lib.pymaker.pymaker import Address
from lib.pymaker.pymaker.numeric import Wad, Ray

@pytest.fixture
def token1():
    return Address('0x0101010101010101010101010101010101010101')


@pytest.fixture
def token2():
    return Address('0x0202020202020202020202020202020202020202')



def test_nicely_convert_to_string_without_amounts(token1, token2):
    # given
    conversion = Conversion(token1, token2, Ray.from_number(1.01), Wad.from_number(1000), 'met()')

    # expect
    assert str(conversion) == "[0x0101010101010101010101010101010101010101 -> 0x0202020202020202020202020202020202020202 @1.010000000000000000000000000 by met() (max=1000.000000000000000000 0x0101010101010101010101010101010101010101)]"




