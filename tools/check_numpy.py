import sys
import os
import traceback

print("PYTHON_EXE:", sys.executable)
print("PYTHON_VERSION:", sys.version.replace('\n', ' '))
print("CWD:", os.getcwd())
print("--- sys.path ---")
for p in sys.path:
    print(p)
print("--- end sys.path ---")

def try_import(name):
    try:
        mod = __import__(name)
        print(f"IMPORT_OK: {name} ->", getattr(mod, '__file__', '<built-in>'))
    except Exception as e:
        print(f"IMPORT_FAIL: {name} -> {e}")
        traceback.print_exc()

print('\nTrying import numpy...')
try_import('numpy')

print('\nTrying import numpy._core...')
try_import('numpy._core')

print('\nDone.')
