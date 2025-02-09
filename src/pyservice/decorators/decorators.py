"""Some decorators."""


import typing


def several(factory, number) -> list[typing.Any]:
    stack = []
    for _ in range(number):
        example = factory()
        stack.append(example)
    return stack
