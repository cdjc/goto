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
    globalName = None
    index = 0
    c = fn.__code__

    labels, gotos = find_labels_and_gotos(c)

    # make list from bytestring so we can modify the bytes
    ilist = list(c.co_code)

    # no-op the labels
    for label,(index,_) in labels.items():
        ilist[index:index+7] = [dis.opmap['NOP']]*7

    # change gotos to jumps
    for label,goto_list in gotos.items():
        for index,goto_stack in goto_list:
            if label not in labels:
                raise MissingLabelError("Missing label: {}".format(label))
            base_target,label_stack = labels[label]
            # The label stack should be a subset of the goto stack,
            # but any with, try, or finally block must occur in both.
            if label_stack != goto_stack[:len(label_stack)]:
                raise IllegalGoto('''goto for label "{}" is outside that label's block'''.format(label))
            loop_depth = len(goto_stack) - len(label_stack)
            if loop_depth > 4:
                raise IllegalGoto('''goto cannot jump out more than 4 blocks''')
            non_loop_goto = [x for x in goto_stack if x[0] != 'SETUP_LOOP']
            non_loop_label = [x for x in label_stack if x[0] != 'SETUP_LOOP']
            if non_loop_goto != non_loop_label:
                raise IllegalGoto('label "{}" has goto crossing try, finally, or with boundary'.format(label))
            
            ilist[index:index+loop_depth] = [dis.opmap['POP_BLOCK']]*loop_depth
            target = base_target + 7   # skip NOPs
            jump_index = index+loop_depth
            ilist[jump_index] = dis.opmap['JUMP_ABSOLUTE']
            ilist[jump_index + 1] = target & 255
            ilist[jump_index + 2] = target >> 8

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
    end = len(c.co_code)
    i = 0

    block_stack = []

    # scan through the byte codes to find the labels and gotos
    while i < end:
        op = c.co_code[i]
        i += 1
        name = dis.opname[op]
        
        if name in ('SETUP_LOOP', 'SETUP_WITH','SETUP_FINALLY'):
            block_stack.append((name, i))
        elif name == 'SETUP_EXCEPT':
            block_stack.append((name, i))
            block_stack.append(('BLOCK', i))
        elif name in ('POP_BLOCK', 'POP_EXCEPT'):
            block_stack.pop()
        
        if op > dis.HAVE_ARGUMENT:
            b1 = c.co_code[i]
            b2 = c.co_code[i+1]
            num = b2 * 256 + b1

            if name == 'LOAD_GLOBAL':
                # remember global name in case a LOAD_ATTR follows
                global_name = c.co_names[num]
                index = i - 1
                i += 2
                continue
                
            if name == 'LOAD_ATTR':
                label_name = c.co_names[num]
                if global_name == 'label':
                    if label_name in labels:
                        raise DuplicateLabelError('Label "{}" appears more than once'.format(label_name))
                    labels[label_name] = index, tuple(block_stack)
                elif global_name == 'goto':
                    if label_name not in gotos:
                        gotos[label_name] = []
                    gotos[label_name].append((index, tuple(block_stack)))
                    
            name = None
            i += 2
    return labels, gotos
