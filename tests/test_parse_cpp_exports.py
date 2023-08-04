import ctypes_wrapper as cw
import tempfile

def dump_str_to_file(content):
    tmp = tempfile.NamedTemporaryFile(delete = False)
    with open(tmp.name, "w") as handle:
        handle.write(content)
    return tmp.name

def test_parse_cpp_exports_basic():
    # Just some basic pointers here and there.
    tmp = dump_str_to_file("""
//[[export]]
int foobar(X x, const YYY y, const long double* z, char*** aaron, const char* const* becky) {
    return 1
}""")

    output = cw.parse_cpp_exports([tmp])
    assert "foobar" in output
    res, args = output["foobar"]

    assert res.full_type == "int"
    assert res.base_type == "int"
    assert res.pointer_level == 0

    assert args[0].name == "x"
    assert args[0].type.full_type == "X"
    assert args[0].type.base_type == "X"
    assert args[0].type.pointer_level == 0

    assert args[1].name == "y"
    assert args[1].type.full_type == "const YYY"
    assert args[1].type.base_type == "YYY"
    assert args[1].type.pointer_level == 0

    assert args[2].name == "z"
    assert args[2].type.full_type == "const long double*"
    assert args[2].type.base_type == "long double"
    assert args[2].type.pointer_level == 1 

    assert args[3].name == "aaron"
    assert args[3].type.full_type == "char***"
    assert args[3].type.base_type == "char"
    assert args[3].type.pointer_level == 3

    assert args[4].name == "becky"
    assert args[4].type.full_type == "const char* const*"
    assert args[4].type.base_type == "char"
    assert args[4].type.pointer_level == 2

def test_parse_cpp_exports_whitespace():
    # Add or remove whitespace all over the place.
    tmp = dump_str_to_file("""
//[[export]]
int*foobar( X x, const YYY y , const double * z, char***aaron,const char*const*becky) {
    return 1
}""")

    output = cw.parse_cpp_exports([tmp])
    assert "foobar" in output
    res, args = output["foobar"]

    assert res.full_type == "int*"
    assert res.base_type == "int"
    assert res.pointer_level == 1

    assert args[0].name == "x"
    assert args[0].type.full_type == "X"
    assert args[0].type.base_type == "X"
    assert args[0].type.pointer_level == 0

    assert args[1].name == "y"
    assert args[1].type.full_type == "const YYY"
    assert args[1].type.base_type == "YYY"
    assert args[1].type.pointer_level == 0

    assert args[2].name == "z"
    assert args[2].type.full_type == "const double*"
    assert args[2].type.base_type == "double"
    assert args[2].type.pointer_level == 1 

    assert args[3].name == "aaron"
    assert args[3].type.full_type == "char***"
    assert args[3].type.base_type == "char"
    assert args[3].type.pointer_level == 3

    assert args[4].name == "becky"
    assert args[4].type.full_type == "const char* const*"
    assert args[4].type.base_type == "char"
    assert args[4].type.pointer_level == 2

def test_parse_cpp_exports_cpp():
    # Add templates, type inference and references.
    tmp = dump_str_to_file("""
//[[export]]
std::vector<decltype(bar)>foobar( decltype(FOO)x, const std::list<std::vector<int> >& y , std::map<int, char**> z, std::vector<double>&aaron, const std::vector<char>*becky) {
    return 1
}""")

    output = cw.parse_cpp_exports([tmp])
    assert "foobar" in output
    res, args = output["foobar"]

    assert res.full_type == "std::vector<decltype(bar)>"
    assert res.base_type == "std::vector<decltype(bar)>"
    assert res.pointer_level == 0

    assert args[0].name == "x"
    assert args[0].type.full_type == "decltype(FOO)"
    assert args[0].type.base_type == "decltype(FOO)"
    assert args[0].type.pointer_level == 0

    assert args[1].name == "y"
    assert args[1].type.full_type == "const std::list<std::vector<int> >&"
    assert args[1].type.base_type == "std::list<std::vector<int> >"
    assert args[1].type.pointer_level == 0

    assert args[2].name == "z"
    assert args[2].type.full_type == "std::map<int, char**>"
    assert args[2].type.base_type == "std::map<int, char**>"
    assert args[2].type.pointer_level == 0 

    assert args[3].name == "aaron"
    assert args[3].type.full_type == "std::vector<double>&"
    assert args[3].type.base_type == "std::vector<double>"
    assert args[3].type.pointer_level == 0

    assert args[4].name == "becky"
    assert args[4].type.full_type == "const std::vector<char>*"
    assert args[4].type.base_type == "std::vector<char>"
    assert args[4].type.pointer_level == 1



