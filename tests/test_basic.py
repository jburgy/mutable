#-*-coding:utf8;-*-

from mutable import mutates, scope
from unittest import TestCase, main

class MutableTest(TestCase):

    def setUp(self):
        @mutates
        def fib(n):
            return n if n<2 else fib(n-1)+fib(n-2)
        self.fib = fib

    def tearDown(self):
        del self.fib

    def test_update(self):
        fib  = self.fib
        fib5 = fib.ref(5)
        fib7 = fib.ref(7)
        self.assertIsNone(fib5())
        self.assertIsNone(fib7())
        self.assertEqual(fib(7), 13)
        self.assertEqual(fib(5), 5)
        self.assertIsNotNone(fib5())
        self.assertIsNotNone(fib7())
        self.assertIn(fib7(), fib5().callers)
        with scope:
            self.assertEqual(fib(5), 5)
            self.assertEqual(fib(7), 13)
            fib5.value = 3
            with self.assertRaises(AttributeError):
                fib5.value
            self.assertIsNotNone(fib5())
            self.assertIsNotNone(fib7())  # created by shadowing
            self.assertEqual(set(), fib5().callers)  # new entry never called
            self.assertEqual(fib(5), 3)  # overridden
            self.assertEqual(fib(7), 9)
            self.assertIn(fib7(), fib5().callers)
        self.assertIn(fib7(), fib5().callers)
        
    def test_edges(self):
        fib = self.fib
        @mutates
        def f(n):
            return -n
        @mutates
        def g(n):
            return f(fib(n))
        
        f3 = f.ref(3)
        f5 = f.ref(5)
        g5 = g.ref(5)
        fib5 = fib.ref(5)
        self.assertIsNone(f5())
        self.assertEqual(g(5), -5)
        self.assertIn(g5(), f5().callers)
        self.assertIn(g5(), fib5().callers)
        with scope:
            fib5.value = 3
            with self.assertRaises(AttributeError):
                fib5.value
            self.assertNotIn(g5(), f5().callers)
            self.assertNotIn(g5(), fib5().callers)
            self.assertEqual(fib(5), 3)
            self.assertEqual(g(5), -3)
            self.assertIn(g5(), f3().callers)  # predicate caller
            self.assertIn(g5(), fib5().callers)
        self.assertIsNone(f3())
        with self.assertRaises(AttributeError):
            f3().callers
    
    def test_garbage(self):
        from gc import garbage, collect
    
        @mutates
        def collatz(m, n):
            return n if m==1 else collatz(3*m+1 if m&1 else m//2, n+1)
           
        self.assertEqual(collatz(17, 0), 12)
        self.assertIn(collatz.ref(17, 0)(), collatz.ref(52, 1)().callers)
        del collatz
        collect()
        self.assertEqual([], garbage)
        
    def _test_indirection(self, f, g, h, collatz, g27_value=None):
        c27 = collatz.ref(27)
        f27 = f.ref(27)
        g27 = g.ref(27)
        h27 = h.ref(27)
        self.assertEqual(collatz(27), 82)
        self.assertIn(c27(), f27().callers)
        self.assertIn(c27(), g27().callers)
        self.assertIsNone(h27())
        with scope:
            g27.value = g27_value
            with self.assertRaises(AttributeError):
                g27.value
            self.assertEqual(collatz(27), 13)
            self.assertIsNotNone(f27())  # still valid!
            self.assertIn(c27(), g27().callers)
            self.assertIn(c27(), h27().callers)
        self.assertIsNone(h27())  # still invalid in this scope!
        # potential optimization: unlift terminals (in no callers)
        
    def test_edges2(self):
        'create edge with if'
        f = mutates(lambda n: 3*n+1)
        g = mutates(lambda n: n&1)
        h = mutates(lambda n: n//2)
        c = mutates(lambda n: f(n) if g(n) else h(n))
        
        self._test_indirection(f, g, h, c, g27_value=False)
    
    def test_edges3(self):
        'create edge with function indirection'
        f = mutates(lambda n: 3*n+1)
        g = mutates(lambda n: f if n&1 else g)
        h = mutates(lambda n: n//2)
        c = mutates(lambda n: g(n)(n))
        
        self._test_indirection(f, g, h, c, g27_value=h)

if '__main__' == __name__:
    main()
