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
