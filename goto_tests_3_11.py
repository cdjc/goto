import unittest

from goto import goto
from goto import DuplicateLabelError, GotoNotWithinLabelBlock, GotoNestedTooDeeply, MissingLabelError


class MyTestCase(unittest.TestCase):

    def test_simple(self):
        @goto
        def simple():
            a = 5
            goto .done
            a = 7
            label .done
            self.assertEqual(5, a)

        simple()

    def test_two_gotos(self):
        @goto
        def two_gotos(n):
            if n == 1:
                goto .done
            n = 5
            goto .done
            n = 2
            label .done
            return n
        self.assertEqual(1, two_gotos(1))
        self.assertEqual(5, two_gotos(99))

    def test_two_labels(self):
        got_exception = False
        try:
            @goto
            def two_labels():
                goto .done

                label .done
                label .done
        except DuplicateLabelError:
            got_exception = True
        self.assertTrue(got_exception)

    def test_not_in_label_block(self):
        got_exception = False
        try:
            @goto
            def not_in_label_block():
                goto .here
                for i in (1,2):
                    label .here
        except GotoNotWithinLabelBlock:
            got_exception = True
        self.assertTrue(got_exception)

    def test_pop_iter_in_loop(self):
        @goto
        def pop_iter_in_loop():
            count = 0

            label.repeat
            count += 1
            if count == 5000:  # will probably crash if POP_TOPs aren't accurate

                return True

            for x in [1]:
                if x == 1:
                    goto.repeat
            return False

        pop_iter_in_loop()

    def test_deep_nest(self):
        @goto
        def deep_nest():
            for _ in [1]:
                for _ in [1]:
                    for _ in [1]:
                        for _ in [1]:
                            for _ in [1]:
                                for _ in [1]:
                                    for _ in [1]:
                                        for _ in [1]:
                                            goto.here
            if __name__: return False
            label .here
            return True

        self.assertTrue(deep_nest())

    def test_too_deep_nest(self):
        got_exception = False
        try:
            @goto
            def deep_nest():
                for _ in [1]:
                    for _ in [1]:
                        for _ in [1]:
                            for _ in [1]:
                                for _ in [1]:
                                    for _ in [1]:
                                        for _ in [1]:
                                            for _ in [1]:
                                                for _ in [1]:
                                                    for _ in [1]:
                                                        for _ in [1]:
                                                            for _ in [1]:
                                                                goto .here
                if __name__: return False
                label .here
                return True
        except GotoNestedTooDeeply:
            got_exception = True
        self.assertTrue(got_exception)

    def test_not_in_same_block(self):
        got_exception = False
        try:
            @goto
            def not_in_same_block():
                for _ in [1]:
                    for _ in [1]:
                        goto .here
                    for _ in [1]:
                        label .here
        except GotoNotWithinLabelBlock:
            got_exception = True
        self.assertTrue(got_exception)

    def test_goto_missing_label(self):
        got_exception = False
        try:
            @goto
            def goto_missing_label():
                goto .there
                label .here
        except MissingLabelError:
            got_exception = True
        self.assertTrue(got_exception)

    def test_unreachable_code_suggestion(self):
        got_exception = False
        try:
            @goto
            def goto_unreachable_code():
                goto .after_return
                return 5
                label .after_return  # Python will remove 'unreachable' code
                return 10
        except MissingLabelError:
            got_exception = True
        self.assertTrue(got_exception)

    def test_example(self):
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

        val = matrix_find([[[1,2]],[[3,4]]], 3)
        self.assertEqual("found", val)

    def test_ext_arg_back(self):
        @goto
        def ext_arg_back():
            def z():
                pass
            n = 0
            j = 0
            label .start  # 12 instructions
            n += 1  # 5 instructions
            dir(z)  # 15 instructions each that do nothing
            dir(z)
            dir(z)
            dir(z)
            dir(z)
            dir(z)
            dir(z)
            dir(z)
            dir(z)
            dir(z)

            # 167 instructions past label 12+5+10*15

            dir(z)
            dir(z)
            dir(z)
            dir(z)

            # 227 ins. past label

            # code before goto is 21 instructions
            if n == 2:
                return n  # Here if we jumped back to the start label
            j += 1
            if j == 2:
                return n  # Probably here if we jumped back short of the start label

            # 248 past label

            pass  # 249  +1 instruction
            pass  # 250
            pass  # 251
            pass  # 252
            pass  # 253
            pass  # 254
            pass  # 255

            # 256 (+ 1 because we jump after the label.)
            goto .start  # we will actually jump back 257 because +1 for the extended arg.
            return -1  # Shouldn't ever get here

        import dis
        dis.dis(ext_arg_back)
        self.assertEqual(2, ext_arg_back())

    def test_no_ext_arg_back(self):
        @goto
        def no_ext_arg_back():
            def z():
                pass
            n = 0
            j = 0
            label .start  # 12 instructions
            n += 1  # 5 instructions
            dir(z)  # 15 instructions each that do nothing
            dir(z)
            dir(z)
            dir(z)
            dir(z)
            dir(z)
            dir(z)
            dir(z)
            dir(z)
            dir(z)

            # 167 instructions past label 12+5+10*15

            dir(z)
            dir(z)
            dir(z)
            dir(z)

            # 227 ins. past label

            # code before goto is 21 instructions
            if n == 2:
                return n  # Here if we jumped back to the start label
            j += 1
            if j == 2:
                return n  # Probably here if we jumped back short of the start label

            # 248 past label

            pass  # 249  +1 instruction
            pass  # 250
            pass  # 251
            pass  # 252
            pass  # 253
            pass  # 254

            # 255 (+ 1 because we jump after the label.)
            goto .start
            return -1  # Shouldn't ever get here

        import dis
        dis.dis(no_ext_arg_back)
        self.assertEqual(2, no_ext_arg_back())

if __name__ == '__main__':
    unittest.main()
