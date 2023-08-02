#!/usr/bin/python3

from .parse_cpp_exports import *
from .create_cpp_bindings import *
from .create_py_bindings import *

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        prog='Create ctypes wrappers',
        description="""
    This script runs through a directory of C++ source files and pulls out all
    function definitions marked with an `// [[export]]` header. It then creates
    wrapper files in C++ and Python to bind the exported functions with correct
    types and exception handling. This mimics the behavior of `Rcpp::compile()`,
    which does the same thing for C++ bindings in R packages.""")

    parser.add_argument("srcdir", type=str, help="Source directory for the C++ files.")
    parser.add_argument("--py", dest="pypath", type=str, default="ctypes_bindings.py", help="Output path for the Python-side bindings.")
    parser.add_argument("--cpp", dest="cpppath", type=str, default="ctypes_bindings.cpp", help="Output path for the C++-side bindings.")
    parser.add_argument("--dll", dest="dllname", type=str, default="core", help="Prefix of the DLL.")
    parser.add_argument("--typedp", dest="typed_ptr", action="store_true", default=False, help="Whether pointers should be explicitly typed. If false, all pointers are considered to be void*.")
    parser.add_argument("--numpy", dest="auto_numpy", action="store_true", default=False, help="Whether Numpy bindings should be auto-generated. This allows contiguous NumPy arrays to be directly passed to the generated functions.")
    cmd_args = parser.parse_args()

    all_functions = parse_cpp_exports(cmd_args.srcdir)
    create_cpp_bindings(all_functions, cmd_args.cpppath)
    create_py_bindings(all_functions, cmd_args.pypath, cmd_args.dllname, typed_pointers = cmd_args.typed_ptr, auto_numpy = cmd_args.auto_numpy)
