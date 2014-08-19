goto
====

An implementation of goto for Python 3.

Usage:

```python
from goto import goto

@goto
def test(n):
   
    s = 0

    label .myLoop

    if n <= 0:
        return s
    s += n
    n -= 1

    goto .myLoop
```
