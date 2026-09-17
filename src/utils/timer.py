from time import perf_counter


def timer():
    return perf_counter()


def elapsed(start):
    return perf_counter() - start


def print_duration(label, start):
    print(f"{label:<40} {elapsed(start):>8.2f} s")