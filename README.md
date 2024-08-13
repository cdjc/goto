goto
====

An implementation of goto for Python 3.

Not for production use. It's a bit of fun. Some people have used it to port old goto-containing code.

Instructions
------------

1. Copy `goto.py` where your code can import it.
2. Import the goto decorator from the goto module with `from goto import goto`
3. Identify the function you want to use goto within, and decorate it with `@goto`
4. Within the function, you can specify labels like so: `label .found` (use whatever label you want, `found` is just an example)
5. In the code, you can do a jump to the label with `goto .found` (or whatever your label is called)

Multiple gotos can target one label. Every goto must have a target label.

Usage example:

```python
from goto import goto

@goto
def matrix_find(matrix, n):
    for rectangle in matrix:
        for line in rectangle:
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
