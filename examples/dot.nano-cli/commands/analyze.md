# Analyze

Perform a detailed analysis of code, text, or data.

## Prompt Template

Please perform a comprehensive analysis of the following: $ARGUMENTS

Your analysis should include:
1. Structure and organization assessment
2. Quality evaluation
3. Potential issues or areas for improvement
4. Strengths and positive aspects
5. Specific recommendations for enhancement

Provide detailed insights with concrete examples where applicable.

## Usage

```bash
nano-cli /analyze "code or content to analyze"
nano-cli /analyze src/main.py
```

## Examples

```bash
# Analyze a Python file
nano-cli /analyze "$(cat app.py)"

# Analyze a concept
nano-cli /analyze "the architecture of this microservice"
```

## Notes

This command provides in-depth analysis useful for code reviews, content evaluation, and system assessment.