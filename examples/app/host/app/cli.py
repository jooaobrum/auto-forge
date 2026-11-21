import sys


def total(numbers: list[str]) -> int:
    return sum(int(n) for n in numbers)


if __name__ == "__main__":
    print(total(sys.argv[1:]))
