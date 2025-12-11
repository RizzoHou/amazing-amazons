# Task Completion Workflow

This workflow should be executed each time a task is completed.

## Workflow Steps

### 1. Update Memory Bank

Update the memory bank to reflect changes made during the task:

- Review ALL memory bank files to ensure they reflect current state
- Update `activeContext.md` with:
  - Recent changes made
  - Current work focus
  - Next steps
  - Any new patterns or insights discovered
- Update `progress.md` with:
  - What was accomplished
  - What's now working
  - Any new known issues
- Update other relevant memory bank files as needed:
  - `projectbrief.md` if core requirements, scope, or goals evolved
  - `systemPatterns.md` if architecture or patterns changed
  - `techContext.md` if technologies or setup changed
  - `productContext.md` if requirements or understanding evolved

**See detailed workflow**: `.clinerules/workflows/memory_bank_update.md`

### 2. Update README

Keep README.md synchronized with current project state:

- Update after major features, milestones, or structural changes
- Focus on user-facing sections:
  - **Current Status**: Align with progress.md milestones
  - **Setup/Installation**: Keep steps accurate and tested
  - **Usage**: Update commands and examples
  - **Project Structure**: Reflect actual file organization
- Keep README concise and user-focused (detailed docs belong elsewhere)
- Test any commands or examples before committing

**See detailed workflow**: `.clinerules/workflows/readme_update.md`

### 3. Clear Git Status Output

Clean up the git working directory:

```bash
git add .
git status
```

Review the staged changes, then commit with a descriptive message:

```bash
git commit -m "descriptive message about what changed and why"
```

After committing, verify clean status:

```bash
git status
```

The output should show "nothing to commit, working tree clean".

**See detailed workflow**: `.clinerules/workflows/git_status_clear.md`

## Execution Notes

- This workflow ensures continuity between sessions by maintaining accurate memory bank state
- Clean git status helps track what's been completed and what remains
- Always commit with clear, descriptive messages that explain the changes
- If changes span multiple logical commits, make separate commits for each logical grouping

---

**Workflow Trigger**: Execute this workflow when you see task completion or when explicitly requested by the user.
