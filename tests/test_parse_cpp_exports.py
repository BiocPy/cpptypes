import cpptypes as cw
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

    # Just some basic pointers here and there.
    tmp = dump_str_to_file("""
//[[export]]
int* empty() {
    return NULL
}""")

    output = cw.parse_cpp_exports([tmp])
    assert "empty" in output
    res, args = output["empty"]

    assert res.full_type == "int*"
    assert res.base_type == "int"
    assert res.pointer_level == 1

    assert len(args) == 0

def test_parse_cpp_exports_whitespace():
    # Add or remove whitespace all over the place.
    tmp = dump_str_to_file("""
//[[export]]
int*foobar( X x, const YYY y , const 
    double * z, char***aaron,const char*const*becky) {
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
std::vector<decltype(bar)>foobar( decltype(FOO)x, const std::list<std::vector<int> >& y , std::map<int, 
    char**> z, // adding some extra whitespace and C++-style comments!
    std::vector<double>&aaron, const std::vector<char>*becky,
    decltype(a/b) div // seeing what happens if we add a '/' sign outside of a comment.
    ) {
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

def test_parse_cpp_exports_tags():
    # Add templates, type inference and references.
    tmp = dump_str_to_file("""
//[[export]]
unsigned short/** asd */ foobar/**goody*/(/**whee*/int x,
    const char/**numpy*/* y , long /* not a tag */ long z, double* /** multiple tags here */ aaron, char becky/** yay imavoid* */,
    std::vector</** asdsad */ int> catherine /* non-base-level tags are ignored, as is this comment. */) {
    return 1
}""")

    output = cw.parse_cpp_exports([tmp])
    assert "foobar" in output
    res, args = output["foobar"]

    assert res.full_type == "unsigned short"
    assert res.base_type == "unsigned short"
    assert res.pointer_level == 0
    assert ["asd", "goody"] == sorted(res.tags)

    assert args[0].name == "x"
    assert args[0].type.full_type == "int"
    assert args[0].type.base_type == "int"
    assert args[0].type.pointer_level == 0
    assert ["whee"] == list(args[0].type.tags)

    assert args[1].name == "y"
    assert args[1].type.full_type == "const char*"
    assert args[1].type.base_type == "char"
    assert args[1].type.pointer_level == 1
    assert ["numpy"] == list(args[1].type.tags)

    assert args[2].name == "z"
    assert args[2].type.full_type == "long long"
    assert args[2].type.base_type == "long long"
    assert args[2].type.pointer_level == 0
    assert len(args[2].type.tags) == 0

    assert args[3].name == "aaron"
    assert args[3].type.full_type == "double*"
    assert args[3].type.base_type == "double"
    assert args[3].type.pointer_level == 1
    assert ["here", "multiple", "tags"] == sorted(list(args[3].type.tags))

    assert args[4].name == "becky"
    assert args[4].type.full_type == "char"
    assert args[4].type.base_type == "char"
    assert args[4].type.pointer_level == 0 
    assert ["imavoid*", "yay"] == sorted(args[4].type.tags)

    assert args[5].name == "catherine"
    assert args[5].type.full_type == "std::vector<int>"
    assert args[5].type.base_type == "std::vector<int>"
    assert args[5].type.pointer_level == 0
    assert len(args[5].type.tags) == 0

def test_parse_cpp_exports_failed():
    tmp = dump_str_to_file("""
//[[export]]
int foobar(X x, const YYY y, const long double* z, char*** aaron,""")

    err = None
    try:
        cw.parse_cpp_exports([tmp])
    except Exception as exc:
        err = exc
    assert err is not None
    assert str(err.__cause__).startswith("reached end of the file")

    tmp = dump_str_to_file("""
//[[export]]
int foobar(X x, const std::vector<int> > y,""")

    err = None
    try:
        cw.parse_cpp_exports([tmp])
    except Exception as exc:
        err = exc
    assert err is not None
    assert str(err.__cause__).startswith("imbalanced angle brackets")
