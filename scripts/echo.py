import sys

# Echo the first argument or a default message
message = sys.argv[1] if len(sys.argv) > 1 else "Hello from Echo"
print(message)
