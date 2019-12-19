import dis
import struct
from types import CodeType
from typing import Tuple


def new_code(fc, *, argcount=None, posonlyargcount=None, kwonlyargcount=None, nlocals=None, stacksize=None, flags=None,
             code_=None, consts=None, names=None, varnames=None, filename=None, name=None, firstlineno=None,
             lnotab=None, freevars=None, cellvars=None):
    # I could use fc.replace but I prefer having a utility function since it's easier to debug
    return CodeType(
        argcount or fc.co_argcount,
        posonlyargcount or fc.co_posonlyargcount,
        kwonlyargcount or fc.co_kwonlyargcount,
        nlocals or fc.co_nlocals,
        stacksize or fc.co_stacksize,
        flags or fc.co_flags,
        code_ or fc.co_code,
        consts or fc.co_consts,
        names or fc.co_names,
        varnames or fc.co_varnames,
        filename or fc.co_filename,
        name or fc.co_name,
        firstlineno or fc.co_firstlineno,
        lnotab or fc.co_lnotab,
        freevars or fc.co_freevars,
        cellvars or fc.co_cellvars
    )


def new_instruction(instr, *, opname=None, opcode=None, arg=None, argval=None, argrepr=None, offset=None, starts_line=None, is_jump_target=None):
    # Creates a new instruction since namedtuples aren't mutable
    return dis.Instruction(
        opname or instr.opname,
        opcode or instr.opcode,
        arg or instr.arg,
        argval or instr.argval,
        argrepr or instr.argrepr,
        offset or instr.offset,
        starts_line or instr.starts_line,
        is_jump_target or instr.is_jump_target
    )


def merge_code(original: CodeType, added: CodeType) -> Tuple[CodeType, bytes]:
    # Merges consts, varnames and names (though names probably isn't useful here)
    # It also takes the max stack size of the two and increases it by 1 to be safe.
    all_consts = list(original.co_consts)
    all_varnames = list(original.co_varnames)
    all_names = list(original.co_names)
    remapped_instructions = []
    for instruction in dis.get_instructions(added):
        if instruction.opcode in dis.hasconst:
            if instruction.argval in all_consts:
                instruction = new_instruction(instruction, arg=all_consts.index(instruction.argval))
            else:
                instruction = new_instruction(instruction, arg=len(all_consts))
                all_consts.append(instruction.argval)
        elif instruction.opcode in dis.haslocal:
            if instruction.argval in all_varnames:
                instruction = new_instruction(instruction, arg=all_varnames.index(instruction.argval))
            else:
                instruction = new_instruction(instruction, arg=len(all_varnames))
                all_varnames.append(instruction.argval)
        elif instruction.opcode in dis.hasname:
            if instruction.argval in all_names:
                instruction = new_instruction(instruction, arg=all_names.index(instruction.argval))
            else:
                instruction = new_instruction(instruction, arg=len(all_names))
                all_names.append(instruction.argval)
        remapped_instructions.append(instruction)
    return (new_code(original,
                     consts=tuple(all_consts),
                     names=tuple(all_names),
                     varnames=tuple(all_varnames),
                     stacksize=max([original.co_stacksize, added.co_stacksize])+1),
            b"".join(struct.pack("BB", b.opcode, b.arg or 0) for b in remapped_instructions))
