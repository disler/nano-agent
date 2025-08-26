# Refactor

Suggest improvements and refactoring for code to enhance quality and maintainability.

## Prompt Template

Please review and suggest refactoring improvements for the following code: $ARGUMENTS

Focus on:
1. Code organization and structure
2. Naming conventions and clarity
3. Performance optimizations
4. Best practices and design patterns
5. Error handling and edge cases
6. Documentation and comments
7. Testability improvements

Provide the refactored code with explanations for each change.

## Usage

```bash
nano-cli /refactor "code to refactor"
nano-cli /refactor "$(cat messy_code.py)"
```

## Examples

```bash
# Refactor a function
nano-cli /refactor "def calc(x,y): return x+y*2"

# Refactor a class
nano-cli /refactor "$(cat legacy_class.py)"
```

## Notes

This command helps improve code quality by suggesting modern best practices and cleaner implementations.