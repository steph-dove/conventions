"""Example of untyped Python code."""


def add(a, b):
    return a + b


def multiply(x, y):
    result = x * y
    return result


def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result


class Calculator:
    def __init__(self, precision):
        self.precision = precision

    def add(self, a, b):
        return round(a + b, self.precision)

    def subtract(self, a, b):
        return round(a - b, self.precision)

    def multiply(self, a, b):
        return round(a * b, self.precision)

    def divide(self, a, b):
        return round(a / b, self.precision)


def helper_function(x):
    return x * 2


def another_helper(data):
    return [item for item in data if item is not None]
