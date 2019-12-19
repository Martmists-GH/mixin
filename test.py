from mixin import mixin, inject, at, redirect


class Test:
    x = 1

    def run(self):
        print(self.x)
        return self.x


@mixin(Test)
class TestMixin:
    x: int

    @inject(method="run", at=at("HEAD"))
    def run_head(self):
        # This code runs before any of the code in Test.run, though other mixins may precede it
        self.x = 3

    @inject(method="run", at=at("RETURN"))
    def run_return(self):
        # Note: This runs right before the return, so `self.x` has already been loaded onto the stack. This means that
        # The function will still return 3 instead of 10
        # For this reason, the stack size is increased by one in merge_stack.
        # additionally, this is currently only applied to the last return
        self.x = 10


if __name__ == "__main__":
    t = Test()
    res = t.run()
    print("Returned:", res)
    print("t.x:", t.x)
    import dis
    dis.dis(t.run)
