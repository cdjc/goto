#!/usr/bin/env python3
import dis
import sys
import types


class MissingLabelError(Exception):
    """'goto' without matching 'label'."""
    pass


class DuplicateLabelError(Exception):
    '''Label appears more than once'''
    pass


class IllegalGoto(Exception):
    pass


class GotoNotWithinLabelBlock(Exception):
    pass


class JumpTooFar(Exception):
    # TODO Should fix this with extended args
    pass


class GotoNestedTooDeeply(Exception):
    pass


def goto_pre311(fn):
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

    labels, gotos = find_labels_and_gotos_pre311(c)

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


def find_labels_and_gotos_pre311(code):
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


class Label:

    def __init__(self, name, load_global_idx, load_attr_idx, stack):
        self.name = name
        self.load_global_idx = load_global_idx
        self.load_attr_idx = load_attr_idx
        self.stack = stack
        self.gotos = []
        self.target_idx = None  # fill this in when we NOP the instructions. Should point to the last NOP

    def add_goto(self, load_global_idx, load_attr_idx, stack):
        # label stack must be prefix of goto stack
        if len(stack) < len(self.stack):
            raise GotoNotWithinLabelBlock()
        if not all(x[0] == x[1] for x in zip(self.stack, stack)):
            raise GotoNotWithinLabelBlock()
        pops_needed = len(stack) - len(self.stack)
        self.gotos.append((load_global_idx, load_attr_idx, pops_needed))


def find_labels_and_gotos3_11(code) -> dict[Label]:
    labels = {}
    gotos = {}

    for_iter_stack = []  # instruction number of the FOR_ITERs that we have seen. pop when we se a corresponding JUMP_BACKWARD

    for ins in dis.get_instructions(code):
        if ins.opname == 'FOR_ITER':
            for_iter_stack.append(ins.offset)
        elif ins.opname == 'JUMP_BACKWARD' and for_iter_stack and ins.argval == for_iter_stack[-1]:
            for_iter_stack.pop()
        elif ins.opname == 'LOAD_GLOBAL':
            global_name = ins.argval
            index = ins.offset
            continue
        elif ins.opname == 'LOAD_ATTR':
            label = ins.argval
            if global_name.lower() == 'label':
                if label in labels:
                    raise DuplicateLabelError('Label "{}" appears more than once'.format(label))
                labels[label] = index, ins.offset, tuple(
                    for_iter_stack)
            elif global_name.lower() == 'goto':
                if label not in gotos:
                    gotos[label] = []
                gotos[label].append(
                    (index, ins.offset, tuple(for_iter_stack)))  # XXX (load_global, load_attr, stack of get_attr)

    hanging_goto = gotos.keys() - labels.keys()
    if len(hanging_goto) != 0:
        raise MissingLabelError(
            f"Goto missing labels: {', '.join(hanging_goto)}. Python may have removed 'unreachable' code. Use 'if __name__: return' instead of 'return'")

    label_objs = {}
    for label in labels:
        label_objs[label] = Label(label, *labels[label])

    for goto_label in gotos:
        for load_global, load_attr, stack in gotos[goto_label]:
            label_objs[goto_label].add_goto(load_global, load_attr, stack)

    return label_objs


def goto3_11(fn):
    '''

    '''
    c = fn.__code__

    labels: dict[Label] = find_labels_and_gotos3_11(c)

    # make list from bytestring so we can modify the bytes
    ilist = list(c.co_code)

    globals_to_nop = []
    attrs_to_nop = []

    load_global_cache_count = dis._inline_cache_entries[dis.opmap['LOAD_GLOBAL']]
    load_attr_cache_count = dis._inline_cache_entries[dis.opmap['LOAD_ATTR']]

    # no-op the labels (and the CACHEs too otherwise it won't work)
    for label in labels.values():
        globals_to_nop.append(label.load_global_idx)
        attrs_to_nop.append(label.load_attr_idx)
        label.target_idx = label.load_attr_idx + load_attr_cache_count * 2 + 2 # 2 bytes per instruction
        for lglobal, lattr, _ in label.gotos:
            globals_to_nop.append(lglobal)
            attrs_to_nop.append(lattr)

    for index in globals_to_nop:
        for nopi in range(load_global_cache_count + 1):  # + 1 for the instruction itself
            ilist[index + nopi * 2] = 9

    for index in attrs_to_nop:
        for nopi in range(load_attr_cache_count + 1 + 1):  # + 1 for the instruction itself +1 for POP_TOP
            ilist[index + nopi * 2] = 9

    # add in the JUMPs

    for label in labels.values():
        for goto_index, _, pops_needed in label.gotos:
            index = goto_index
            # Check that we can fit enough POP_TOPs
            # NOTE: The +2 means we always assume we have to add a single EXTENDED_ARG
            if ilist[index + pops_needed * 2 + 2] != dis.opmap['NOP']:
                raise GotoNestedTooDeeply()
            for i in range(pops_needed):
                ilist[index] = dis.opmap['POP_TOP']
                ilist[index + 1] = 0
                index += 2
            # diff = (index - label.load_global_idx) // 2  # bytecodes are 2 bytes each.
            diff = (index - label.target_idx) // 2  # bytecodes are 2 bytes each.

            if diff > 0:
                diff += 1  # + 1 because it counts from the instruction after the JUMP
                if diff > 255:
                    diff += 1  # we now have to jump over the EXTENDED_ARG instruction too
                    ilist[index] = dis.opmap['EXTENDED_ARG']
                    ilist[index + 1] = diff >> 8  # ignore the lower 8 bits
                    diff &= 255  # only the lower 8 bits
                    index += 2
                ilist[index] = dis.opmap['JUMP_BACKWARD']
                ilist[index + 1] = diff
            else:
                diff = -diff
                diff -= 2  # -1 for EXTENDED_ARG and -1 because it counts from the instruction after the JUMP
                ilist[index] = dis.opmap['EXTENDED_ARG']
                ilist[index + 1] = diff >> 8  # ignore the lower 8 bits

                ilist[index + 2] = dis.opmap['JUMP_FORWARD']
                ilist[index + 3] = diff & 255

    fn.__code__ = fn.__code__.replace(co_code=bytes(ilist))
    return fn


if sys.version_info >= (3, 11):
    goto = goto3_11
else:
    goto = goto_pre311
