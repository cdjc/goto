#!/usr/bin/env python3
import dis
import types


class MissingLabelError(Exception):
    """'goto' without matching 'label'."""
    pass


class DuplicateLabelError(Exception):
    '''Label appears more than once'''
    pass


class IllegalGoto(Exception):
    pass



def goto(fn):
    """
    A function decorator to add the goto command for a function.

    Specify labels like so:

    label .foo
    
    Goto labels like so:

    goto .foo
    
    Rules:
    No jumping out of or into a 'with' block (jumping out could be fixed)
    No jumping out of or into a 'try' or 'finally' block
    Only jump within a loop, or to an outer loop, or to function level.
    No local variables called 'label' or 'goto'
    """
    c = fn.__code__

    labels, gotos = find_labels_and_gotos(c)

    # make list from bytestring so we can modify the bytes
    ilist = list(c.co_code)

    # no-op the labels
    for label, (index, _) in labels.items():
        ilist[index:index + 6] = [dis.opmap['NOP']] * 6

    # change gotos to jumps
    for label, goto_list in gotos.items():
        for index, goto_stack in goto_list:
            if label not in labels:
                raise MissingLabelError("Missing label: {}".format(label))
            base_target, label_stack = labels[label]
            # The label stack should be a subset of the goto stack,
            # but any with, try, or finally block must occur in both.
            if label_stack != goto_stack[:len(label_stack)]:
                raise IllegalGoto(
                    '''goto for label "{}" is outside that label's block'''.format(label))
            loop_depth = len(goto_stack) - len(label_stack)
            if loop_depth > 4:
                raise IllegalGoto('''goto cannot jump out more than 4 blocks''')
            non_loop_goto = [x for x in goto_stack if x[0] != 'SETUP_LOOP']
            non_loop_label = [x for x in label_stack if x[0] != 'SETUP_LOOP']
            if non_loop_goto != non_loop_label:
                raise IllegalGoto(
                    'label "{}" has goto crossing try, finally, or with boundary'.format(label))

            for i in range(loop_depth):
                # TODO: This needs to push future opcodes forwards if loop_depth > 1
                # TODO: ... now that all opcodes take up 2 bytes.
                # TODO: ... absolute/relative jumps will need correcting (might add extended_args!)
                ilist[index + i * 2] = dis.opmap['POP_BLOCK']
            target = base_target + 6  # + 7   # skip NOPs
            jump_index = index + loop_depth * 2
            ilist[jump_index] = dis.opmap['JUMP_ABSOLUTE']
            ilist[jump_index + 1] = target  # TODO: Fix for extended_arg

    # create new code to replace existing function code
    newcode = types.CodeType(c.co_argcount,
                             c.co_kwonlyargcount,
                             c.co_nlocals,
                             c.co_stacksize,
                             c.co_flags,
                             bytes(ilist),
                             c.co_consts,
                             c.co_names,
                             c.co_varnames,
                             c.co_filename,
                             c.co_name,
                             c.co_firstlineno,
                             c.co_lnotab,
                             c.co_freevars,
                             c.co_cellvars)
    fn.__code__ = newcode
    return fn


def find_labels_and_gotos(code):
    '''
    Return map for all labels and gotos in code.
    each mapping is:
        name : (index , block-stack)
    where block-stack is a tuple representing the block stack in the
    function where the label/goto occurs
    '''
    c = code
    labels = {}
    gotos = {}
    global_name: str = None
    index: int = None

    block_stack = []

    for ins in dis.get_instructions(c):
        offset = ins.offset
        if ins.opname in ('SETUP_LOOP', 'SETUP_WITH', 'SETUP_FINALLY'):
            block_stack.append((ins.opname, offset + 1))
            continue
        if ins.opname == 'SETUP_EXCEPT':
            block_stack.append((ins.opname, offset + 1))
            block_stack.append(('BLOCK', offset + 1))
            continue
        if ins.opname in ('POP_BLOCK', 'POP_EXCEPT'):
            block_stack.pop()
            continue
        if ins.opname == 'LOAD_GLOBAL':
            global_name = ins.argval
            index = offset
            continue
        if ins.opname == 'LOAD_ATTR':
            label = ins.argval
            if global_name == 'label':
                if label in labels:
                    raise DuplicateLabelError('Label "{}" appears more than once'.format(label))
                labels[label] = index, tuple(block_stack)
            elif global_name == 'goto':
                if label not in gotos:
                    gotos[label] = []
                gotos[label].append((index, tuple(block_stack)))
    return labels, gotos



def foo(n):
    s = 0

    label .myLoop

    print(s)
    if n <= 0:
        return s
    s += n
    n -= 1

    goto .myLoop

    return s

def find_labels_and_gotos3_11(code):
    labels = {}
    gotos = {}
    for ins in dis.get_instructions(code):
        # XXX find out how nested into for loops we are
        # XXX Maintain stack of GET_ITER locations we'll need to POP_TOP
        # XXX if we want to jump 'up' the stack.
        if ins.opname == 'LOAD_GLOBAL':
            global_name = ins.argval
            index = ins.offset
            continue
        if ins.opname == 'LOAD_ATTR':
            label = ins.argval
            if global_name == 'label':
                if label in labels:
                    raise DuplicateLabelError('Label "{}" appears more than once'.format(label))
                labels[label] = index, ins.offset, tuple([])  # XXX (load_global, load_attr, stack of get_attr)
            elif global_name == 'goto':
                if label not in gotos:
                    gotos[label] = []
                gotos[label].append((index, ins.offset, tuple([])))  # XXX (load_global, load_attr, stack of get_attr)

    hanging_goto = gotos.keys() - labels.keys()
    if len(hanging_goto) != 0:
        raise MissingLabelError(f"Gotos missing labels: {', '.join(hanging_goto)}")

    return labels, gotos

def goto3_11(fn):
    '''

    '''
    c = fn.__code__

    labels, gotos = find_labels_and_gotos3_11(c)

    # make list from bytestring so we can modify the bytes
    ilist = list(c.co_code)

    globals_to_nop = []
    attrs_to_nop = []
    # no-op the labels (and the CACHEs too otherwise it won't work)
    for label, (load_global, load_attr, _) in labels.items():
        globals_to_nop.append(load_global)
        attrs_to_nop.append(load_attr)

    for goto_ls in gotos.values():
        for (load_global, load_attr, _) in goto_ls:
            globals_to_nop.append(load_global)
            attrs_to_nop.append(load_attr)

    for index in globals_to_nop:
        cache_count = dis._inline_cache_entries[dis.opmap['LOAD_GLOBAL']]
        for nopi in range(cache_count+1):  # + 1 for the instruction itself
            ilist[index+nopi*2] = 9

    for index in attrs_to_nop:
        cache_count = dis._inline_cache_entries[dis.opmap['LOAD_ATTR']]
        for nopi in range(cache_count+1+1):  # + 1 for the instruction itself +1 for POP_TOP
            ilist[index+nopi*2] = 9

    #

    for label in gotos:
        for goto_index, _, _ in gotos[label]:
            label_index, _, _ = labels[label]
            diff = (goto_index - label_index) // 2  # bytecodes are 2 bytes each.
            # if abs(diff) > 255 then use EXTENDED_ARG
            if diff > 0:
                ilist[goto_index] = dis.opmap['JUMP_BACKWARD']
                ilist[goto_index + 1] = diff + 1  # + 1 because it counts from the instruction after the JUMP
            else:
                ilist[goto_index] = dis.opmap['JUMP_FORWARD']
                ilist[goto_index + 1] = -diff

    nc = types.CodeType(c.co_argcount,
                        c.co_posonlyargcount,
                        c.co_kwonlyargcount,
                        c.co_nlocals,
                        c.co_stacksize,
                        c.co_flags,
                        bytes(ilist),  # c.co_code,
                        c.co_consts,
                        c.co_names,
                        c.co_varnames,
                        c.co_filename,
                        c.co_name,
                        c.co_qualname,
                        c.co_firstlineno,
                        c.co_linetable,
                        c.co_exceptiontable,
                        c.co_freevars,
                        c.co_cellvars)

    fn.__code__ = nc
    return fn


f = goto3_11(foo)
dis.dis(f, show_caches=True)
print(list(f.__code__.co_code))
print('f = ')
r = f(5)
print(r)
print('Done')