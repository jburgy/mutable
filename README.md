# Mutable (python module)

```mutable.mutates``` is a runtime [call graph](https://en.wikipedia.org/wiki/Call_graph) analysis decorator which lets you manipulate function results like values.  Think of it like a [memoize decorator](https://github.com/ActiveState/code/tree/master/recipes/Python/577219_Minimalistic_Memoization) which remains consistent when you update cached results.  Using it to decorate some of your functions is an easy way to give your script [reactive semantics](https://en.wikipedia.org/wiki/Reactive_programming).

Pretend you are studying the [Australian Broadcasting Corporation](http://www.abc.net.au/) logo in parametric form:
```python
from mutable import mutates, scope
from math import sin, cos, atan2, pi

@mutates
def x(t): return cos(t)

@mutates
def y(t): return sin(3*t)

@mutates
def phi(t): return atan2(x(t), y(t))
```
Now pretend you need to calculate the following partial derivative: ![](https://latex.codecogs.com/gif.latex?\left.\frac{\partial&space;\phi}{\partial&space;x}\right|_{x(t)})

```mutates``` lets you write
```python
def dphi_by_dx(t, epsilon=1e-6):
    x_t = x.ref(t)
    with scope:
        x_t += epsilon
        phi_plus = phi(t)
    with scope:
        x_t -= epsilon
        phi_minus = phi(t)
    return (phi_plus - phi_minus)/(epsilon + epsilon)
```
which is an obvious use of [finite difference](https://en.wikipedia.org/wiki/Finite_difference).

This contrived example illustrates three things ```mutates``` does for you:

1. ```mutates``` caches (```y``` was not invoked by ```dphi_by_dx```)
1. ```mutates``` identifies dependencies automatically (```phi``` was recalculated after each update to ```x```)
1. ```mutates``` cleans up after itself (```scope``` left the original state unperturbed)

Here is, at a high level, how it works. ```mutates``` does not create one cache per decorated function like the [minimalistic memoization recipe](https://github.com/ActiveState/code/tree/master/recipes/Python/577219_Minimalistic_Memoization). It defines a unique global list of caches instead to simplify scope management. The global list of caches is a [ChainMap](https://docs.python.org/3/library/collections.html#collections.ChainMap) _and_ a [context manager](https://docs.python.org/3/reference/datamodel.html#context-managers). Its only public API is that of a context manager.

Because of Python's very dynamic nature, ```mutates``` detects dependencies between values of decorated functions at runtime. Call graph analysis is a side-effect of _every_ decorated call, even those that hit the cache. It is also scope-sensitive by necessity. This point is key to understand how mutable avoids inconsistencies between _pure_ and mutated cache entries. Any operations which modifies a cache entry _shadows_ all entries which depend on it directly or indirectly. Shadowing creates blank entries in the innermost scope while leaving alone those in outer scopes.

Decorated functions implement a ```ref``` method which accepts the same signature as them and returns a reference to the corresponding cache entries. The cache entry can be retrieved in the current scope by calling the reference object, just like the standard [weakref](https://docs.python.org/3/library/weakref.html#module-weakref) model. The call returns [None](https://docs.python.org/3/library/constants.html#None) if the entry has not yet been created in the current scope. References delegate all in-place operators as well as a write-only 'value' property. As mentioned earlier, any modification (setting value or invoking in-place operators) _shadows_ the entry and the transitive closure of its callers in the current scope. 

This interactive session breaks down each step:
```python
>>> t = pi/4
>>> phi(t)  # establishes dependencies as side-effect
0.7853981633974483
>>> x_t = x.ref(t)  # x_t is a reference to x(t) in cache
>>> with scope:  # create fresh scope to avoid trampling results and dependencies
...     x_t += 1e-6 # shadow x(t) and phi(t), update x(t)
...     phi_plus = phi(t)  # evaluate phi using updated x(t) and original y(t)
...

>>> phi_plus - phi(t)  # exiting scope recovers original values
7.071062811947471e-07
```
