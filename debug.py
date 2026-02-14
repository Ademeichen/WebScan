
import os
import sys

print("Starting debug.py")
try:
    with open("debug.txt", "w") as f:
        f.write("Debug script ran successfully.\n")
        f.write(f"CWD: {os.getcwd()}\n")
    print("Wrote to debug.txt")
except Exception as e:
    print(f"Failed to write: {e}")
