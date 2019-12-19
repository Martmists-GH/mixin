import dis
import inspect

from code_utils import new_code, merge_code


class MixinTarget:
    def __init__(self, fname, func, at, inject_type):
        self.fname = fname
        self.func = func
        self.at = at
        self.inject_type = inject_type

    def apply(self, target_cls):
        # Apply the injection
        if self.inject_type in ("override", "redirect"):
            # Just add it, though maybe __slots__ could cause issues here?
            setattr(target_cls, self.fname, self.func)

        elif self.inject_type == "inject":
            original_func = getattr(target_cls, self.fname)
            original_code = original_func.__code__
            if any(x in dis.hasjabs for x in original_code.co_code):
                # TODO
                raise Exception("Absolute jumps are not supported yet!")
            removed_returns = self.func.__code__.co_code
            # Remove all returns from the new code
            while b"S\x00" in removed_returns:
                index = removed_returns.find(b"S\x00")
                # TODO: Fix jumps
                removed_returns = removed_returns[:index-2] + removed_returns[index+2:]

            # Merge the consts and stuff, and get remapped bytes
            # We could just join the two tuples, but it'd be a waste of resources
            added_code = new_code(self.func.__code__, code_=removed_returns)
            merged_code, remapped_bytes = merge_code(original_code, added_code)

            # At-specific injections
            if self.at[0] == "HEAD":
                # TODO: hasjabs will fail
                new_bytes = remapped_bytes + original_code.co_code
                result_code = new_code(merged_code, code_=new_bytes)
            elif self.at[0] == "RETURN":
                # TODO: hasjabs will fail
                new_bytes = original_code.co_code + remapped_bytes
                result_code = new_code(merged_code, code_=new_bytes)
            else:
                raise Exception(f"Unsupported at: {self.at[0]}")
            # TODO:
            # - allow cancelling of the method
            # - ???
            original_func.__code__ = result_code

    def __repr__(self):
        # Debug repr
        return "<MixinTarget '{0.func}' '{0.at}' '{0.inject_type}'>".format(self)


def mixin(cls):
    def decorator(mixin_cls):
        for (name, param) in inspect.getmembers(mixin_cls):
            if isinstance(param, MixinTarget):
                print(param)
                param.apply(cls)
        return mixin_cls
    return decorator


def inject(*, method, at, cancellable=False):
    def decorator(func):
        return MixinTarget(method, func, at, "inject")
    return decorator


def redirect(*, method, at):
    def decorator(func):
        return MixinTarget(method, func, at, "redirect")
    return decorator


def at(value, method="", ordinal=None):
    """
    possible values for `value`:
    HEAD - start of function
    RETURN - end of function
    INVOKE - method call
    FIELD - attribute getter/setter
    JUMP - jump opcodes (injects before)
    INVOKE_ASSIGN - function call that has its value stored somewhere, injected after assignment
    """
    return value, method, ordinal
