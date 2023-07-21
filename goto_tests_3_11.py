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


if __name__ == '__main__':
    unittest.main()
