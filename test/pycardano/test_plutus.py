from dataclasses import dataclass
from test.pycardano.util import check_two_way_cbor
from typing import Union

import pytest

from pycardano.exception import DeserializeException, SerializeException
from pycardano.plutus import (
    COST_MODELS,
    ExecutionUnits,
    PlutusData,
    Redeemer,
    RedeemerTag,
)
from pycardano.serialization import IndefiniteList


@dataclass
class MyTest(PlutusData):
    CONSTR_ID = 130

    a: int
    b: bytes
    c: IndefiniteList
    d: dict


@dataclass
class BigTest(PlutusData):
    CONSTR_ID = 8

    test: MyTest


@dataclass
class LargestTest(PlutusData):
    CONSTR_ID = 9


@dataclass
class VestingParam(PlutusData):
    CONSTR_ID = 1

    beneficiary: bytes
    deadline: int
    testa: Union[BigTest, LargestTest]
    testb: Union[BigTest, LargestTest]


@dataclass
class MyRedeemer(Redeemer):
    data: MyTest


def test_plutus_data():
    """Ground truth of this test is generated by test/resources/haskell/PlutusData. See its README for more details."""
    key_hash = bytes.fromhex("c2ff616e11299d9094ce0a7eb5b7284b705147a822f4ffbd471f971a")
    deadline = 1643235300000
    testa = BigTest(MyTest(123, b"1234", IndefiniteList([4, 5, 6]), {1: b"1", 2: b"2"}))
    testb = LargestTest()

    my_vesting = VestingParam(
        beneficiary=key_hash, deadline=deadline, testa=testa, testb=testb
    )
    assert (
        "d87a9f581cc2ff616e11299d9094ce0a7eb5b7284b705147a822f4ffbd471f971a1b0000017e9"
        "874d2a0d905019fd8668218829f187b44313233349f040506ffa2014131024132ffffd9050280ff"
        == my_vesting.to_cbor()
    )
    check_two_way_cbor(my_vesting)


def test_plutus_data_json():
    key_hash = bytes.fromhex("c2ff616e11299d9094ce0a7eb5b7284b705147a822f4ffbd471f971a")
    deadline = 1643235300000
    testa = BigTest(MyTest(123, b"1234", IndefiniteList([4, 5, 6]), {1: b"1", 2: b"2"}))
    testb = LargestTest()

    my_vesting = VestingParam(
        beneficiary=key_hash, deadline=deadline, testa=testa, testb=testb
    )

    encoded_json = my_vesting.to_json(separators=(",", ":"))

    assert (
        '{"constructor":1,"fields":[{"bytes":"c2ff616e11299d9094ce0a7eb5b7284b705147a822f4ffbd471f971a"},'
        '{"int":1643235300000},{"constructor":8,"fields":[{"constructor":130,"fields":[{"int":123},'
        '{"bytes":"31323334"},{"list":[{"int":4},{"int":5},{"int":6}]},{"map":[{"v":{"bytes":"31"},'
        '"k":{"int":1}},{"v":{"bytes":"32"},"k":{"int":2}}]}]}]},{"constructor":9,"fields":[]}]}'
        == encoded_json
    )

    assert my_vesting == VestingParam.from_json(encoded_json)


def test_plutus_data_to_json_wrong_type():
    test = MyTest(123, b"1234", IndefiniteList([4, 5, 6]), {1: b"1", 2: b"2"})
    test.a = "123"
    with pytest.raises(TypeError):
        test.to_json()


def test_plutus_data_from_json_wrong_constructor():
    test = (
        '{"constructor": 129, "fields": [{"int": 123}, {"bytes": "31323334"}, '
        '{"list": [{"int": 4}, {"int": 5}, {"int": 6}]}, {"map": [{"v": {"bytes": "31"}, '
        '"k": {"int": 1}}, {"v": {"bytes": "32"}, "k": {"int": 2}}]}]}'
    )
    with pytest.raises(DeserializeException):
        MyTest.from_json(test)

    test2 = (
        '{"constructor":1,"fields":[{"bytes":"c2ff616e11299d9094ce0a7eb5b7284b705147a822f4ffbd471f971a"},'
        '{"int":1643235300000},{"constructor":22,"fields":[{"constructor":130,"fields":[{"int":123},'
        '{"bytes":"31323334"},{"list":[{"int":4},{"int":5},{"int":6}]},{"map":[{"v":{"bytes":"31"},'
        '"k":{"int":1}},{"v":{"bytes":"32"},"k":{"int":2}}]}]}]},{"constructor":23,"fields":[]}]}'
    )
    with pytest.raises(DeserializeException):
        VestingParam.from_json(test2)


def test_plutus_data_from_json_wrong_data_structure():
    test = (
        '{"constructor": 130, "fields": [{"int": 123}, {"bytes": "31323334"}, '
        '{"wrong_list": [{"int": 4}, {"int": 5}, {"int": 6}]}, {"map": [{"v": {"bytes": "31"}, '
        '"k": {"int": 1}}, {"v": {"bytes": "32"}, "k": {"int": 2}}]}]}'
    )
    with pytest.raises(DeserializeException):
        MyTest.from_json(test)


def test_plutus_data_from_json_wrong_data_structure_type():
    test = (
        '[{"constructor": 130, "fields": [{"int": 123}, {"bytes": "31323334"}, '
        '{"list": [{"int": 4}, {"int": 5}, {"int": 6}]}, {"map": [{"v": {"bytes": "31"}, '
        '"k": {"int": 1}}, {"v": {"bytes": "32"}, "k": {"int": 2}}]}]}]'
    )
    with pytest.raises(TypeError):
        MyTest.from_json(test)


def test_plutus_data_hash():
    assert (
        bytes.fromhex(
            "923918e403bf43c34b4ef6b48eb2ee04babed17320d8d1b9ff9ad086e86f44ec"
        )
        == PlutusData().hash().payload
    )


def test_redeemer():
    data = MyTest(123, b"234", IndefiniteList([4, 5, 6]), {1: b"1", 2: b"2"})
    redeemer = MyRedeemer(RedeemerTag.SPEND, data, ExecutionUnits(1000000, 1000000))
    assert (
        "840000d8668218829f187b433233349f040506ffa2014131024132ff821a000f42401a000f4240"
        == redeemer.to_cbor()
    )
    check_two_way_cbor(redeemer)


def test_cost_model():
    assert (
        "a141005901d59f1a000302590001011a00060bc719026d00011a000249f01903e800011"
        "a000249f018201a0025cea81971f70419744d186419744d186419744d186419744d1864"
        "19744d186419744d18641864186419744d18641a000249f018201a000249f018201a000"
        "249f018201a000249f01903e800011a000249f018201a000249f01903e800081a000242"
        "201a00067e2318760001011a000249f01903e800081a000249f01a0001b79818f7011a0"
        "00249f0192710011a0002155e19052e011903e81a000249f01903e8011a000249f01820"
        "1a000249f018201a000249f0182001011a000249f0011a000249f0041a000194af18f80"
        "11a000194af18f8011a0002377c190556011a0002bdea1901f1011a000249f018201a00"
        "0249f018201a000249f018201a000249f018201a000249f018201a000249f018201a000"
        "242201a00067e23187600010119f04c192bd200011a000249f018201a000242201a0006"
        "7e2318760001011a000242201a00067e2318760001011a0025cea81971f704001a00014"
        "1bb041a000249f019138800011a000249f018201a000302590001011a000249f018201a"
        "000249f018201a000249f018201a000249f018201a000249f018201a000249f018201a0"
        "00249f018201a00330da70101ff" == COST_MODELS.to_cbor()
    )
