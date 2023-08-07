import cpptypes as cw
import tempfile

def test_create_cpp_bindings():
    exports = {
        "akari_best_function": (
            cw.CppType("void*", "void", 1, set()), 
            [
                cw.CppArgument("akira", cw.CppType("double", "double", 0, set())),
                cw.CppArgument("alice", cw.CppType("void*", "void", 1, set()))
            ]
        ),
        "ai_second_function": (
            cw.CppType("int", "int", 0, set()),
            [
                cw.CppArgument("alicia", cw.CppType("const char*", "char", 1, set())),
                cw.CppArgument("athena", cw.CppType("long double", "long double", 0, set()))
            ]
        )
    }

    path = tempfile.NamedTemporaryFile(delete = False)
    cw.create_cpp_bindings(exports, path.name)

    has_akari_decl = False
    has_ai_decl = False
    has_akari_def = False
    has_ai_def = False
    with open(path.name, "r") as handle:
        for line in handle:
            line = line.rstrip()
            if line == "void* akari_best_function(double, void*);":
                has_akari_decl = True
            elif line == "int ai_second_function(const char*, long double);":
                has_ai_decl = True
            elif line == "PYAPI void* py_akari_best_function(double akira, void* alice, int32_t* errcode, char** errmsg) {":
                has_akari_def = True
            elif line == "PYAPI int py_ai_second_function(const char* alicia, long double athena, int32_t* errcode, char** errmsg) {":
                has_ai_def = True

    assert has_akari_decl
    assert has_ai_decl
    assert has_akari_def
    assert has_ai_def
