<!-- These are examples of badges you might want to add to your README:
     please update the URLs accordingly

[![Built Status](https://api.cirrus-ci.com/github/<USER>/cpptypes.svg?branch=main)](https://cirrus-ci.com/github/<USER>/cpptypes)
[![ReadTheDocs](https://readthedocs.org/projects/cpptypes/badge/?version=latest)](https://cpptypes.readthedocs.io/en/stable/)
[![Coveralls](https://img.shields.io/coveralls/github/<USER>/cpptypes/main.svg)](https://coveralls.io/r/<USER>/cpptypes)
[![Conda-Forge](https://img.shields.io/conda/vn/conda-forge/cpptypes.svg)](https://anaconda.org/conda-forge/cpptypes)
[![Monthly Downloads](https://pepy.tech/badge/cpptypes/month)](https://pepy.tech/project/cpptypes)
[![Twitter](https://img.shields.io/twitter/url/http/shields.io.svg?style=social&label=Twitter)](https://twitter.com/cpptypes)
-->

[![Project generated with PyScaffold](https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold)](https://pyscaffold.org/)
[![PyPI-Server](https://img.shields.io/pypi/v/cpptypes.svg)](https://pypi.org/project/cpptypes/)
![Unit tests](https://github.com/BiocPy/cpptypes/actions/workflows/pypi-test.yml/badge.svg)


# Generate ctypes wrappers

## Overview

This script automatically creates the C++ and Python-side wrappers for **ctypes** bindings.
Specifically, we fill `restype` and `argtypes` based on the C++ function signature and we create wrappers to handle C++ exceptions.
We were inspired by the `Rcpp::compile()` function, which does the same for C++ code in R packages.
The aim is to avoid errors from manual binding when developing **ctypes**-based Python packages.

## Install

**cpptypes** is published to [PyPI](https://pypi.org/project/cpptypes/):

```sh
pip install cpptypes
```

## Quick start

To use, add an `// [[export]]` tag above the C++ function to be exported to Python.

```cpp
// [[export]]
int multiply(int a, double b) {
    return a * b;
}
```

We assume that all C++ code is located within a single directory `src`.
We then run the [`cpptypes`](./src/cpptypes/__main__.py) cli provided by this package:

```sh
cpptypes src/ --py bindings.py --cpp bindings.cpp
```

Developers should add `bindings.cpp` to the `Extension` sources in their `setup.py`.
The exported function itself can then be used in Python code with:

```py
from .bindings import * as cxx

cxx.multiply(1, 2)
```

## Handling pointers

Pointers to base types (or `void`) are supported and will be bound with the appropriate **ctypes** pointer type.

```cpp
//[[export]]
void* create_complex_object(int* my_int, double* my_dbl) {
    return reinterpret_cast<void*>(new Something(my_int, my_dbl));
}
```

And then, in Python (assuming we called our Python bindings file `bindings.py`):

```py
import ctypes 
x = ctypes.c_int(100)
y = ctypes.c_double(200)

from .bindings import * as cxx
ptr = cxx.create_complex_object(ctypes.byref(x), ctypes.pointer(y))
```

Void pointers are represented as a (usually 64-bit) integer in Python that can be passed back to C++.
Remember to cast `void*` back to the appropriate type before doing stuff with it!
(For simplicity, we do not support arbitrary pointer types as otherwise we would need to include the header definitions in the `bindings.cpp` file and that would be tedious to track.)

If you want the **ctypes** bindings to treat pointers to base types as `void*`, you can tag the argument with `void_p`.
This means that you can directly pass integer addresses to `my_int` and `my_dbl` in Python rather than casting them to a `ctypes.POINTER` type.

```cpp
//[[export]]
void* create_complex_object2(int* my_int /** void_p */, double* my_dbl /** void_p */) {
    return reinterpret_cast<void*>(new Something(my_int, my_dbl));
}
```

**Note on tags:**
Arguments can be tagged with a `/** xxx yyy zzz */` comment, consisting of space-separated tags that determine how the type should be handled in the wrappers.
(The double `**` is important to distinguish from non-tag comments.)
The tag-containing comment can be inserted anywhere in or next to the argument, e.g., before the type, between the type and the name, after the name but before the comma/parenthesis.
The result type for the function can also be tagged in the same manner.

## Handling NumPy arrays

If we know a certain pointer is derived from a NumPy array, we can add the `numpy` tag to automate type checking and address extraction.

```cpp
//[[export]]
void* create_complex_object3(int32_t* my_int /** numpy */, double* my_dbl /** numpy */) {
    return reinterpret_cast<void*>(new Something(my_int, my_dbl));
}
```

Then, in Python, we can just pass the arrays directly to the bound function:

```py
import numpy
x = numpy.random.rand(1000).astype(numpy.int32)
y = numpy.random.rand(1000).astype(numpy.double)
cxx.create_complex_object3(x, y)
```

This will check that the NumPy arrays correspond to the specified type before calling the C++ function.
It is best to use fixed-width integers rather than relying on machine-dependent aliases like `int`, `short`, etc.

The wrapper functions will also check that the arrays are contiguous in memory.
If you want to support non-contiguous arrays, add the `non_contig` tag to the relevant arguments.

The `numpy` tag is only relevant to function arguments and not return values.
Use the `numpy.ctypeslib.as_array()` function to convert a **ctypes** pointer to a **numpy** array of the relevant type.

## Known limitations

- Not all **ctypes** types are actually supported, mostly out of laziness.
