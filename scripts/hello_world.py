import dagger
import sys

@dagger.function
def hello_world(name: str) -> str:
    return f"Hello, {name}!"

# Script expects one argument for the name
name = sys.argv[1] if len(sys.argv) > 1 else "World"
print(hello_world(name))
