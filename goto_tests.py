#!/usr/bin/env python3

from goto import *

if __name__ == '__main__':
    
    # simple test
    @goto
    def test1(n):

        s = 0

        label .myLoop

        if n <= 0:
            return s
        s += n
        n -= 1

        goto .myLoop

    test1(10)

    # jump out of loop
    @goto
    def test2():
        n = 500
        matrix = []
        for i in range(n):
            matrix.append(list(range(n*i, n*(i+1))))
            
        
        for ls in matrix:
            for num in ls:
                if num == 1234:
                    #print('Found it')
                    goto .foundIt
        
        # didn't find it
        assert(False)

        label .foundIt       
        assert(True)

    #Illegal jump from except block into try block
    try:
        @goto
        def test_try_2():
            try:
                label .foo
            except:
                goto .foo
            finally:
                pass
    except IllegalGoto:
        assert(True)
    else:
        assert(False)
        
    got_exception = False
    
    # Illegal jump into try block
    try:
        @goto
        def test_try_cross():
            try:
                label .foo
            except:
                pass
            
            goto .foo
        
    except IllegalGoto:
        got_exception = True
    finally:
        assert(got_exception)
        
    # Jump out of loop multiple times
    @goto
    def test_block_stack():
        
        count = 0
        
        label .repeat
        count += 1
        
        if count == 50: # will die at 21 if we don't POP_BLOCK
            assert(True)
            return
        
        for x in [1]:
            if x == 1:
                goto .repeat
                label .b
                x = 2
    test_block_stack()

    # Illegal jump into loop
    try:
        got_exception = False
        @goto
        def test_block_underflow():
            
            for x in [1]:
                label .bad
                
            goto .bad
    except IllegalGoto:
        assert(True)
    else:
        assert(False)
        
    # Jump out of nested loop (4 levels)
    @goto
    def nested():
        for x1 in [1]:
            for x2 in [2]:
                for x3 in [3]:
                    for x4 in [4]:
                        goto .done
        label .done

    print(dis.dis(nested))
    # Illegal to jump out of >4 levels of nesting
    try:
        @goto
        def nested5():
            for x1 in [1]:
                for x2 in [2]:
                    for x3 in [3]:
                        for x4 in [4]:
                            for x5 in [5]:
                                goto .done
            label .done
    except IllegalGoto:
        assert(True)
    else:
        assert(False)
    
    # Illegal to have two labels
    try:
        @goto
        def double_label():
            label .foo
            label .foo
    except DuplicateLabelError:
        assert(True)
    else:
        assert(False)
            
    class wither:
        def __enter__(self): pass
        def __exit__(self, _1, _2, _3): pass
    
    # jump out of loop, within a 'with' block
    @goto
    def with_test():
        with wither() as w:
            for x in [1]:
                goto .foo
            label .foo
        a=2

    @goto
    def simple(n):
        goto .skip
        print(n)
        label .skip
    
    @goto
    def double():
        n = 0
        label .start
        n += 1
        if n >= 10:
            return
        if n%2 == 0:
            goto .start
        print (n)
        goto .start

    double()

    #@goto
    def loop():
        for i in 'foo':
            goto .done
        label .done

    class FunctionStateMachine:
        
        def __init__(self, limit):
            self.n = 0
            self.limit = limit
            
        def state_odd(self):
            self.n += 1
            return self.state_even
            
        def state_even(self):
            if self.n == self.limit:
                return None
            self.n += 1
            return self.state_odd
            
        def go(self):
            state = self.state_even
            while state:
                state = state()
    
    @goto
    def goto_state_machine(limit):
        
        n = 0

        #################
        label .state_even
    
        if n == limit:
            return
        n += 1
        goto .state_odd # not really necessary
        
        ################
        label .state_odd
        
        n += 1
        goto .state_even
        
    
    def while_loop(limit):
        n = 0
        while n != limit:
            n += 1
            n += 1
            

    assert(test1(10) == 55)
    test2()
    test_block_stack()
    nested()
    with_test()
    #print(dis.dis(goto_state_machine))
    #print(dis.dis(while_loop))
    limit = 10000000
    from time import process_time
    start = process_time()
    goto_state_machine(limit)
    end = process_time()
    print("goto:",end-start)
    func = FunctionStateMachine(limit)
    start = process_time()
    func.go()
    end = process_time()
    print("func:",end-start)
    start = process_time()
    while_loop(limit)
    #n = 0
    #while n != limit:
        #n += 1
        #n += 1
    end = process_time()
    print("while:", end-start)
    
