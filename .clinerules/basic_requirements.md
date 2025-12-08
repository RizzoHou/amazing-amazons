# Basic Requirements for Development

## Initial Setup
If you are new to this project, explore it thoroughly to gain a comprehensive understanding of the codebase, architecture, and workflow before making changes.

## Documentation Standards

- **Feature Documentation**: Update relevant documentation in `docs/` when modifying or adding features to ensure documentation stays synchronized with code changes.

- **Memory Bank Maintenance**: Update relevant documentation in `memorybank/` throughout the development process to maintain accurate project context and enable effective future sessions.

- **Document Decisions and Rationale**: Maintain thorough documentation practices. Document your decisions, changes, and rationale as you work to provide context for future development.

- **README Currency**: Keep `README.md` current with project progress, setup instructions, and usage information to help new users and developers get started quickly.

## Development Workflow

- **Long-Running Commands**: Use `nohup` for commands that cannot be executed quickly or need to run in the background, ensuring they continue after terminal disconnection.

- **Python Environment**: Always activate the virtual environment with `source venv/bin/activate` before running Python scripts to ensure correct dependency resolution.

- **Incremental Development**: Break large coding tasks into smaller components. Complete and test each component individually before proceeding to the next, ensuring each part is production-ready before moving forward.

- **Incremental File Creation**: When creating large files (documentation, code files, etc.), build them section by section using multiple tool calls. Start with `write_to_file` for the initial structure, then use `replace_in_file` to add subsequent sections. This approach ensures reliability and prevents failures from attempting to generate excessive content in a single operation.

- **File Organization**: Maintain a clean and organized file hierarchy. Place files in appropriate directories according to their purpose and function within the project.

## Version Control

- **Git Commits**: Use git after every major change to the project. Commit frequently with clear, descriptive messages that explain what changed and why.

---

**Note**: These requirements help maintain code quality, project organization, and development continuity across sessions.
