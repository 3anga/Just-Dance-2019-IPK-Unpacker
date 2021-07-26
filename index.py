from ipk import *
import sys

while True:
    print("""Welcome to Just Dance 2019 IPK Unpacker
    [1] Extract files
    [2] Pack files""")

    answer = int(input("> "))

    if answer == 1:
        file = input("Your IPK: ")
        directory = input("Output directory: ")
        extract(file, directory)
        sys.exit(1)
    elif answer == 2:
        file = input("Your directory: ")
        directory = input("Output IPK: ")
        extract(file, directory)
        sys.exit(1)