#!/usr/bin/python3

import argparse
import os

from .parse_cpp_exports import parse_cpp_exports
from .create_cpp_bindings import create_cpp_bindings
from .create_py_bindings import create_py_bindings

def find_cpp_files(location, found):
    for f in os.scandir(location):
        if f.is_dir():
            find_cpp_files(f.path, found)
        elif f.path.lower().endswith(".cpp") or f.path.lower().endswith(".cc"):
            found.append(f.path)

def main():
    parser = argparse.ArgumentParser(
        prog = "cpptypes",
        description="""This script runs through a directory of C++ source files and pulls out all function definitions marked with an `// [[export]]` header. 
It then creates wrapper files in C++ and Python to bind the exported functions with correct types and exception handling. 
This mimics the behavior of `Rcpp::compile()`, which does the same thing for C++ bindings in R packages."""
    )

    parser.add_argument(
        "srcdir", 
        type=str, 
        help="Source directory for the C++ files. This is searched recursively for all *.cpp and *.cc files."
    )
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
        "--dll", 
        dest="dllname", 
        type=str, 
        default="core", 
        help="Prefix of the DLL."
    )
    cmd_args = parser.parse_args()

    all_files = []
    find_cpp_files(cmd_args.srcdir, all_files)

    all_functions = parse_cpp_exports(all_files)
    create_cpp_bindings(all_functions, cmd_args.cpppath)
    create_py_bindings(all_functions, cmd_args.pypath, cmd_args.dllname)

if __name__ == "__main__":
    main()

