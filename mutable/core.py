# -*-coding:utf8;-*-
from functools import wraps


class _Scope:
    def __init__(self):
        self.caches = [{}]

    def search(self, func, key, offset=0):
        for cache in self.caches[offset:]:
            try:
                return cache[func, key]
            except KeyError:
                pass
        raise KeyError(func, key)

    def insert(self, func, key):
        self.caches[0][func, key] = entry = Entry(func, key)
        return entry

    def __enter__(self):
        self.caches.insert(0, {})

    def __exit__(self, type, value, traceback):
        self.caches.pop(0)


scope = _Scope()


class _Delegate(type):
    def __init__(cls, name, bases, namespace):
        def delegate(opname):
            attr = "__{}__".format(opname)

            def delegated(self, other):
                entry, orig_value = self._shadow()
                entry._value = getattr(orig_value, attr)(other)
                return self

            return delegated

        for opname in "add and concat floordiv lshift mod mul or pow rshift sub truediv xor".split():
            setattr(cls, "__i{}__".format(opname), delegate(opname))


class Entry(metaclass=_Delegate):
    __slots__ = "wrapper", "key", "callers", "_value"

    def __init__(self, wrapper, key):
        self.wrapper = wrapper
        self.key = key
        self.callers = set()

    def __call__(self, _scope=scope):
        try:
            return _scope.search(self.wrapper, self.key)
        except KeyError:
            return None

    def _shadow(self, _scope=scope):
        wrapper = self.wrapper
        key = self.key
        try:
            orig = _scope.search(wrapper, key, offset=1)
            orig_value = orig._value
        except (AttributeError, KeyError):
            orig_value = None
        else:
            for caller in orig.callers:
                caller._shadow()
        return _scope.insert(wrapper, key), orig_value

    def _setvalue(self, value):
        entry, _ = self._shadow()
        entry._value = value

    value = property(None, _setvalue)

    def __repr__(self):
        try:
            value = self._value
        except AttributeError:
            value = None
        return "{}{}->{}".format(self.wrapper.__name__, self.key, value)


def mutates(wrapped, _scope=scope, stack=[]):
    """Wrap callable in a consistent mutable cache

    >>> ncalls=0
    >>> @mutates
    ... def fib(n):
    ...     global ncalls
    ...     ncalls += 1
    ...     return n if n<2 else fib(n-1)+fib(n-2)

    >>> fib(7), ncalls
    (13, 8)
    >>> with scope:
    ...     fib.ref(5).value = 3
    ...     ncalls=0
    ...     res = fib(7), ncalls

    >>> res
    (9, 2)
    >>> ncalls=0; fib(7), ncalls
    (13, 0)
    """

    @wraps(wrapped)
    def wrapper(*args):
        try:
            entry = _scope.search(wrapper, args)
        except KeyError:
            entry = _scope.insert(wrapper, args)
        entry.callers.update(stack[-1:])
        try:
            return entry._value
        except AttributeError:  # invalid Entry -> fallthru
            pass
        stack.append(entry)
        try:
            value = wrapped(*args)
        finally:
            stack.pop()
        entry._value = value
        return value

    wrapper.ref = lambda *args: Entry(wrapper, args)  # type: ignore[attr-access]
    return wrapper


if __name__ == "__main__":
    from doctest import testmod

    testmod()
