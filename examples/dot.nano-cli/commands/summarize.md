# Summarize

Generate a concise summary of the specified content.

## Prompt Template

Please provide a comprehensive summary of the following content: $ARGUMENTS

Include:
1. Main topics or themes
2. Key points and findings
3. Important details or takeaways
4. A brief conclusion

Be concise but thorough, aiming for a summary that captures the essence of the content.

## Usage

```bash
nano-cli /summarize "content to summarize"
nano-cli /summarize README.md
```

## Examples

```bash
# Summarize a file
nano-cli /summarize "$(cat README.md)"

# Summarize a topic
nano-cli /summarize "the concept of machine learning"
```

## Notes

This command is useful for quickly understanding the main points of documents, articles, or any text content.