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
        self.x = 3

    @inject(method="run", at=at("RETURN"))
    def run_return(self):
        # Note: This run right before the return, so `self.x` has already been loaded onto the stack. This means that
        # The function will still return 3 instead of 10
        # For this reason, the stack size is increased by one in merge_stack.
        self.x = 10


if __name__ == "__main__":
    res = Test().run()
    print("Returned:", res)
