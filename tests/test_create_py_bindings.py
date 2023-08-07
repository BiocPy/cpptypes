import cpptypes as cw
from cpptypes.create_py_bindings import map_cpp_type, create_py_bindings
import tempfile

def test_map_cpp_type():
    assert map_cpp_type(cw.CppType("void*", "void", 1, set())) == "ct.c_void_p"
    assert map_cpp_type(cw.CppType("char*", "char", 1, set())) == "ct.c_char_p"
    assert map_cpp_type(cw.CppType("uintptr_t*", "uintptr_t", 1, set())) == "ct.c_void_p"
    assert map_cpp_type(cw.CppType("char**", "char", 2, set())) == "ct.POINTER(ct.c_char_p)"
    assert map_cpp_type(cw.CppType("int*", "int", 1, set())) == "ct.POINTER(ct.c_int)"
    assert map_cpp_type(cw.CppType("int**", "int", 2, set())) == "ct.POINTER(ct.POINTER(ct.c_int))"
    assert map_cpp_type(cw.CppType("int**", "int", 2, set(["void_p"]))) == "ct.c_void_p"
    assert map_cpp_type(cw.CppType("double*", "double", 1, set())) == "ct.POINTER(ct.c_double)"
    assert map_cpp_type(cw.CppType("double*", "double", 1, set(["numpy"]))) == "ct.c_void_p"

    assert map_cpp_type(cw.CppType("uintptr_t", "uintptr_t", 0, set())) == "ct.c_void_p"
    assert map_cpp_type(cw.CppType("double", "double", 0, set())) == "ct.c_double"
    assert map_cpp_type(cw.CppType("float", "float", 0, set())) == "ct.c_float"
    assert map_cpp_type(cw.CppType("int", "int", 0, set())) == "ct.c_int"
    assert map_cpp_type(cw.CppType("int", "int", 0, set())) == "ct.c_int"
    assert map_cpp_type(cw.CppType("int32_t", "int32_t", 0, set())) == "ct.c_int32"
    assert map_cpp_type(cw.CppType("uint64_t", "uint64_t", 0, set())) == "ct.c_uint64"

    assert map_cpp_type(cw.CppType("signed char", "signed char", 0, set())) == "ct.c_byte"
    assert map_cpp_type(cw.CppType("unsigned char", "unsigned char", 0, set())) == "ct.c_ubyte"
    assert map_cpp_type(cw.CppType("signed int", "signed int", 0, set())) == "ct.c_int"
    assert map_cpp_type(cw.CppType("unsigned long long", "unsigned long long", 0, set())) == "ct.c_ulonglong"
    assert map_cpp_type(cw.CppType("long double", "long double", 0, set())) == "ct.c_longdouble"

    errmsg = ""
    try:
        map_cpp_type(cw.CppType("XXX", "XXX", 0, set())) 
    except Exception as exc:
        errmsg = str(exc)
    assert errmsg.startswith("failed to parse")

    errmsg = ""
    try:
        map_cpp_type(cw.CppType("XXX*", "XXX", 1, set())) 
    except Exception as exc:
        errmsg = str(exc)
    assert errmsg.startswith("failed to parse")


def test_create_py_bindings():
    exports = {
        "cocoa_best_function": (
            cw.CppType("void*", "void", 1, set()), 
            [
                cw.CppArgument("chino", cw.CppType("double*", "double", 1, set(["numpy"]))),
                cw.CppArgument("rize", cw.CppType("void*", "void", 1, set())),
                cw.CppArgument("midori", cw.CppType("const int16_t*", "int16_t", 1, set()))
            ]
        ),
        "syaro_second_function": (
            cw.CppType("int", "int", 0, set()),
            [
                cw.CppArgument("chiya", cw.CppType("const char*", "char", 1, set(["void_p"]))),
                cw.CppArgument("moka", cw.CppType("uint64_t*", "uint64_t", 1, set())),
                cw.CppArgument("maya", cw.CppType("int32_t*", "int32_t", 1, set(["numpy", "non_contig"]))),
                cw.CppArgument("megu", cw.CppType("float*", "float", 1, set(["numpy"])))
            ]
        )
    }

    path = tempfile.NamedTemporaryFile(delete = False)
    create_py_bindings(exports, path.name, "core")

    found_cocoa_types = False
    found_syaro_types = False
    found_cocoa_def = False
    found_syaro_def = False

    with open(path.name, "r") as handle:
        while True:
            line = handle.readline()
            if not line:
                break
            line = line.rstrip()

            if line == "lib.py_cocoa_best_function.restype = ct.c_void_p":
                found_cocoa_types = True
                handle.readline()
                assert handle.readline().strip()[:-1] == "ct.c_void_p"
                assert handle.readline().strip()[:-1] == "ct.c_void_p"
                assert handle.readline().strip()[:-1] == "ct.POINTER(ct.c_int16)"
                assert handle.readline().strip()[:-1] == "ct.POINTER(ct.c_int32)"
                assert handle.readline().strip() == "ct.POINTER(ct.c_char_p)"

            elif line == "lib.py_syaro_second_function.restype = ct.c_int":
                found_syaro_types = True
                handle.readline()
                assert handle.readline().strip()[:-1] == "ct.c_void_p"
                assert handle.readline().strip()[:-1] == "ct.POINTER(ct.c_uint64)"
                assert handle.readline().strip()[:-1] == "ct.c_void_p"
                assert handle.readline().strip()[:-1] == "ct.c_void_p"
                assert handle.readline().strip()[:-1] == "ct.POINTER(ct.c_int32)"
                assert handle.readline().strip() == "ct.POINTER(ct.c_char_p)"

            elif line == "def cocoa_best_function(chino, rize, midori):":
                found_cocoa_def = True
                assert handle.readline().strip() == "return catch_errors(lib.py_cocoa_best_function)(np2ct(chino, np.float64), rize, midori)"

            elif line == "def syaro_second_function(chiya, moka, maya, megu):":
                found_syaro_def = True
                assert handle.readline().strip() == "return catch_errors(lib.py_syaro_second_function)(chiya, moka, np2ct(maya, np.int32, contiguous=False), np2ct(megu, np.float32))"

    assert found_cocoa_types
    assert found_syaro_types
    assert found_cocoa_def
    assert found_syaro_def

    # Again, but without any NumPy exports, and void return types all round.
    for k in exports.keys():
        res, args = exports[k]
        for y in args:
            if "numpy" in y.type.tags:
                y.type.tags.remove("numpy")
        exports[k] = (cw.CppType("void", "void", 0, set()), args)

    create_py_bindings(exports, path.name, "core")

    found_cocoa_types = False
    found_syaro_types = False
    found_cocoa_def = False
    found_syaro_def = False

    with open(path.name, "r") as handle:
        while True:
            line = handle.readline()
            if not line:
                break
            line = line.rstrip()

            if line == "lib.py_cocoa_best_function.restype = None":
                found_cocoa_types = True
                handle.readline()
                assert handle.readline().strip()[:-1] == "ct.POINTER(ct.c_double)"
                assert handle.readline().strip()[:-1] == "ct.c_void_p"
                assert handle.readline().strip()[:-1] == "ct.POINTER(ct.c_int16)"
                assert handle.readline().strip()[:-1] == "ct.POINTER(ct.c_int32)"
                assert handle.readline().strip() == "ct.POINTER(ct.c_char_p)"

            elif line == "lib.py_syaro_second_function.restype = None":
                found_syaro_types = True
                handle.readline()
                assert handle.readline().strip()[:-1] == "ct.c_void_p"
                assert handle.readline().strip()[:-1] == "ct.POINTER(ct.c_uint64)"
                assert handle.readline().strip()[:-1] == "ct.POINTER(ct.c_int32)"
                assert handle.readline().strip()[:-1] == "ct.POINTER(ct.c_float)"
                assert handle.readline().strip()[:-1] == "ct.POINTER(ct.c_int32)"
                assert handle.readline().strip() == "ct.POINTER(ct.c_char_p)"

            elif line == "def cocoa_best_function(chino, rize, midori):":
                found_cocoa_def = True
                assert handle.readline().strip() == "return catch_errors(lib.py_cocoa_best_function)(chino, rize, midori)"

            elif line == "def syaro_second_function(chiya, moka, maya, megu):":
                found_syaro_def = True
                assert handle.readline().strip() == "return catch_errors(lib.py_syaro_second_function)(chiya, moka, maya, megu)"

    assert found_cocoa_types
    assert found_syaro_types
    assert found_cocoa_def
    assert found_syaro_def


