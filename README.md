# Generate ctypes wrappers

## Overview

This script automatically creates the C++ and Python-side wrappers for **ctypes** bindings.
Specifically, we fill `restype` and `argtypes` based on the C++ function signature and we create wrappers to handle C++ exceptions.
We were inspired by the `Rcpp::compile()` function, which does the same for C++ code in R packages.
The aim is to avoid errors from manual binding when developing **ctypes**-based Python packages.

## Quick start

To use, add an `// [[export]]` tag above the C++ function to be exported to Python.

```cpp
// [[export]]
int multiply(int a, double b) {
    return a * b;
}
```

We assume that all C++ code is located within a single directory `src`.
We then run the [`wrap.py`](wrap.py) script:

```cpp
./wrap.py src/ --py bindings.py --cpp bindings.cpp
```

Developers should add `bindings.cpp` to the `Extension` sources in their `setup.py`.
The exported function itself can then be used in Python code with:

```py
from .bindings import * as cxx

cxx.multiply(1, 2)
```

## Handling pointers

Pointers to base types (or `void`) are also supported.
For simplicity, we do not support arbitrary pointer types as otherwise we would need to include the header definitions in the `bindings.cpp` file and that would be tedious to track.

```cpp
//[[export]]
void* create_complex_object(int* int_array, double* more_array) {
    return reinterpret_cast<void*>(new Something(int_array, more_array));
}
```

And then, in Python:

```py
# Mocking up some arrays:
import numpy as np
iarr = (np.random.rand(100) * 10).astype(int)
marr = np.random.rand(100).astype(np.double)

ptr = cxx.create_complex_object(iarr.ctypes.data, marr.ctypes.data)
```

This will be represented as a (usually 64-bit) integer in Python that can be passed back to C++.
For arbitrary pointer types, remember to cast `void*` back to the appropriate type before doing stuff with it.

## Known limitations

- Not all **ctypes** types are actually supported, mostly out of laziness.
- No support for using `byref`, this will probably require some annotation of pointer arguments, e.g., `/* byref */`.
- Remote possibility for a name clash between Python and C++ bindings if there are triple underscores in the latter's argument names.
