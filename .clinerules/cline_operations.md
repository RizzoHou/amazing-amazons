# Cline Operations

Rules to prevent conversation failures and tool-use errors.

## File Creation

- **Incremental File Creation**: When creating large files (documentation, code files, etc.), build them section by section using multiple tool calls. Start with `write_to_file` for the initial structure, then use `replace_in_file` to add subsequent sections. This approach ensures reliability and prevents failures from attempting to generate excessive content in a single operation.
