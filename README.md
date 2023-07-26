goto
====

An implementation of goto for Python 3.

Copy `goto.py` where your code can import it.

Usage:

```python
from goto import goto

@goto
def matrix_find(matrix, n):
    for square in matrix:
        for line in square:
            for value in line:
                if value == n:
                    rval = "found"
                    goto .found
    rval = "not found"
    label .found
    # ... other code here ...
    return rval

print(matrix_find([[[1,2]],[[3,4]]], 3))   # "found"
print(matrix_find([[[1,2]],[[3,4]]], 99))  # "not found"

```
