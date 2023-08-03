#!/usr/bin/python3

import argparse

import ctypes_wrapper.create_cpp_bindings as c1
import ctypes_wrapper.create_py_bindings as c2
import ctypes_wrapper.parse_cpp_exports as p1


def main():
    parser = argparse.ArgumentParser(
        prog="Create ctypes wrappers",
        description="""
    This script runs through a directory of C++ source files and pulls out all
    function definitions marked with an `// [[export]]` header. It then creates
    wrapper files in C++ and Python to bind the exported functions with correct
    types and exception handling. This mimics the behavior of `Rcpp::compile()`,
    which does the same thing for C++ bindings in R packages.""",
    )

    parser.add_argument("srcdir", type=str, help="Source directory for the C++ files.")
    parser.add_argument(
        "--py",
        dest="pypath",
        type=str,
        default="ctypes_bindings.py",
        help="Output path for the Python-side bindings.",
    )
    parser.add_argument(
        "--cpp",
        dest="cpppath",
        type=str,
        default="ctypes_bindings.cpp",
        help="Output path for the C++-side bindings.",
    )
    parser.add_argument(
        "--dll", dest="dllname", type=str, default="core", help="Prefix of the DLL."
    )
    cmd_args = parser.parse_args()

    all_functions = p1.parse_cpp_exports(cmd_args.srcdir)
    c1.create_cpp_bindings(all_functions, cmd_args.cpppath)
    c2.create_py_bindings(all_functions, cmd_args.pypath, cmd_args.dllname)


if __name__ == "__main__":
    main()
