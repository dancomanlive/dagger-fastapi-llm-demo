# Module Naming Conventions

This document outlines the naming conventions used in the `modules` directory of the DaggerFastAPIDemo project.

## Directory Structure

The `modules` directory contains two main subdirectories:

- `scripts/`: Contains standalone Python scripts that are executed inside Dagger containers
- `tools/`: Contains functions that orchestrate Dagger containers and execute the scripts

## Naming Patterns

### Script Files

Files in the `scripts/` directory follow this naming pattern:

```
<functionality>_script.py
```

Examples:
- `hello_script.py`: Script for basic hello world functionality
- `qdrant_script.py`: Script for testing Qdrant connection

### Tool Files

Files in the `tools/` directory follow this naming pattern:

```
<functionality>_tool.py
```

Examples:
- `hello_tool.py`: Tool that invokes the hello script in a Dagger container
- `qdrant_tool.py`: Tool that invokes the Qdrant script in a Dagger container

## Purpose Separation

This convention clearly separates:

1. **Scripts**: Standalone Python scripts that run inside Dagger containers
2. **Tools**: Functions that orchestrate Dagger containers and execute the scripts

## Usage Pattern

1. Tool files import and reference script files
2. The main application imports from tool files
3. Scripts are executed inside containers launched by tools

By following this convention, we ensure the codebase is predictable, maintainable, and easily navigable.
