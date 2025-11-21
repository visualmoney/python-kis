import pytest

from types import SimpleNamespace

import pykis.responses.dynamic as dyn
from pykis.responses.dynamic import (
    KisDynamicScopedPath,
    KisTransform,
    KisList,
    KisObject,
    KisDynamic,
    KisType,
    KisNoneValueError,
)


def test_scoped_path_and_get_scope_on_class_and_instance():
    d = {"outer": {"inner": {"x": 1}}}
    sp = KisDynamicScopedPath("outer.inner")
    assert sp(d) == {"x": 1}

    class A(KisDynamic):
        __path__ = "outer.inner"

    scope = KisDynamicScopedPath.get_scope(A)
    assert isinstance(scope, KisDynamicScopedPath)
    # calling again should return same object (cached)
    scope2 = KisDynamicScopedPath.get_scope(A)
    assert scope is scope2


def test_kis_transform_and_type_repr_and_default_type():
    t = KisTransform(lambda data: data.get("v"))
    # KisType repr
    assert "KisTransform" in repr(t)

    # default_type on simple subclass with __default__ set
    class MyType(KisType):
        __default__ = []

    inst = MyType.default_type()
    assert isinstance(inst, MyType)


def test_kis_list_transform_and_type_error():
    # when input is not a list -> TypeError
    lst = KisList(KisTransform(lambda d: d))
    with pytest.raises(TypeError):
        lst.transform({})

    # when type is KisType instance, its transform is used
    it = KisTransform(lambda d: d * 2)
    lst2 = KisList(it)
    assert lst2.transform([1, 2, 3]) == [2, 4, 6]


def test_kis_object_transform_basic_and_non_dict_and_defaults():
    # non-dict input raises
    with pytest.raises(TypeError):
        KisObject.transform_("not a dict", dict)

    # define a dynamic class with a single field using KisTransform
    class D(KisDynamic):
        a = KisTransform(lambda d: d["a"]) ("a")

    obj = KisObject.transform_({"a": 10}, D)
    assert hasattr(obj, "a") and obj.a == 10

    # missing field without default -> KeyError
    class E(KisDynamic):
        b = KisTransform(lambda d: d.get("b")) ("b")

    with pytest.raises(KeyError):
        KisObject.transform_({}, E)

    # with default supplied via KisTransform __call__
    class F(KisDynamic):
        c = KisTransform(lambda d: d.get("c"))("c", 5)

    objf = KisObject.transform_({}, F)
    assert objf.c == 5


def test_kis_object_transform_with_custom_transform_fn_and_post_init():
    # custom transform path: class defines __transform__ that returns object
    class Custom(KisDynamic):
        def __init__(self):
            self.val = None

        @classmethod
        def __transform__(cls, typ, data):
            o = cls()
            o.val = data.get("z")
            return o

        def __post_init__(self):
            # ensure post_init called
            self.val = (self.val or 0) + 1

    res = KisObject.transform_({"z": 3}, Custom)
    assert isinstance(res, Custom)
    assert res.val == 4


def test_kis_none_value_error_behavior():
    # define a KisType whose transform raises KisNoneValueError
    class BadType(KisType):
        def transform(self, data):
            raise KisNoneValueError()

    class G(KisDynamic):
        g = BadType()

    with pytest.raises(ValueError):
        # Because transform resulted in empty and no nullable, should raise ValueError
        KisObject.transform_({"g": 1}, G)
