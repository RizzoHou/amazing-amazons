# Git Status Clear Workflow

This workflow ensures a clean git working directory after completing tasks. A clean status helps track what's been completed, what's in progress, and maintains a clear project history.

## Why Clean Git Status Matters

### Benefits
- **Clear state tracking**: Know exactly what's committed vs what's being worked on
- **Session boundaries**: Each session ends with a clean slate for the next
- **Better history**: Logical commits make it easier to understand project evolution
- **Easier debugging**: Can revert to known-good states easily
- **Collaboration ready**: Clean status makes sharing work straightforward

### Clean Status Definition
```bash
$ git status
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

## When to Execute

Run this workflow:
1. **After task completion** - Part of task_completion.md workflow
2. **Before switching contexts** - Moving to a different feature/task
3. **After significant changes** - Completed a logical unit of work
4. **User explicitly requests** - "commit changes", "clean git status"
5. **Before ending session** - Leave project in clean state

## Step-by-Step Process

### Step 1: Check Current Status

First, see what changes exist:

```bash
git status
```

**Review the output**:
- Untracked files (in red)
- Modified files (in red)
- Staged files (in green)

### Step 2: Stage Changes

Add all changes to staging area:

```bash
git add .
```

**Alternative - Selective staging**:
If you need to commit changes in logical groups:
```bash
git add path/to/specific/file.py
git add docs/
```

### Step 3: Review Staged Changes

Verify what will be committed:

```bash
git status
```

All files should now show in green under "Changes to be committed".

**Optional - See detailed changes**:
```bash
git diff --staged
```

### Step 4: Commit Changes

Create a commit with a clear, descriptive message:

```bash
git commit -m "descriptive message about what changed and why"
```

See "Commit Message Guidelines" below for best practices.

### Step 5: Verify Clean Status

Confirm the working tree is clean:

```bash
git status
```

Expected output: "nothing to commit, working tree clean"

## Commit Message Guidelines

### Structure

```
type: brief summary (50 chars or less)

Optional detailed explanation if needed:
- Why this change was made
- What problem it solves
- Any important context
```

### Types

- **feat**: New feature or functionality
- **fix**: Bug fix
- **docs**: Documentation changes
- **refactor**: Code restructuring without behavior change
- **test**: Adding or updating tests
- **chore**: Maintenance tasks, dependency updates
- **style**: Code formatting, whitespace changes

### Good Examples

✅ **Specific and clear**:
```bash
git commit -m "feat: implement Alpha-Beta pruning for game tree search"
git commit -m "docs: update README with bot001 deployment status"
git commit -m "fix: correct move validation for edge cases"
git commit -m "refactor: extract board evaluation into separate module"
```

✅ **With context**:
```bash
git commit -m "feat: add C++ bot implementation

- Compiled version for performance improvement
- Uses same algorithm as Python version
- Reduces move calculation time by ~80%"
```

### Bad Examples

❌ **Too vague**:
```bash
git commit -m "updates"
git commit -m "fix stuff"
git commit -m "changes"
```

❌ **Too detailed in first line**:
```bash
git commit -m "Added new Alpha-Beta pruning algorithm with iterative deepening and transposition table for the bot001 implementation which improves performance significantly"
```

## Common Scenarios

### Scenario 1: Single Logical Change

**Situation**: Completed one feature or fix

```bash
git add .
git status          # Review
git commit -m "feat: add move caching for performance optimization"
git status          # Verify clean
```

### Scenario 2: Multiple Logical Changes

**Situation**: Made changes to multiple unrelated parts

**Better approach** - Separate commits:

```bash
# Commit documentation changes
git add README.md docs/
git commit -m "docs: update README with current project status"

# Commit code changes
git add core/ bots/
git commit -m "feat: implement transposition table in bot001"

# Commit config changes
git add .clinerules/
git commit -m "chore: update workflow documentation"

git status  # Verify clean
```

### Scenario 3: Mixed Changes (Code + Generated Files)

**Situation**: Code changes generated logs, cache files, etc.

```bash
# Add only code and docs
git add core/ bots/ docs/ README.md
git commit -m "feat: optimize bot evaluation function"

# Check if anything else needs committing
git status

# If logs/cache should be ignored:
# Add to .gitignore instead
echo "logs/*.log" >> .gitignore
git add .gitignore
git commit -m "chore: ignore log files"
```

### Scenario 4: Work in Progress

**Situation**: Need to pause work but changes aren't complete

**Option A - Commit WIP**:
```bash
git add .
git commit -m "WIP: partial implementation of bot002"
```

**Option B - Stash changes**:
```bash
git stash save "bot002 partial implementation"
git status  # Now clean
# Later: git stash pop
```

## Logical Grouping Guidelines

### When to Split into Multiple Commits

Split changes when:
- ✅ Changes affect unrelated features
- ✅ Documentation updates separate from code changes
- ✅ Bug fixes separate from new features
- ✅ Each change could be reverted independently

### When to Keep in Single Commit

Keep together when:
- ✅ Changes are part of same feature
- ✅ Code and tests for same functionality
- ✅ Refactoring that maintains same behavior
- ✅ Changes depend on each other to work

## Verification Checklist

Before considering git status cleared:

- [ ] Run `git status` and verify output shows "nothing to commit, working tree clean"
- [ ] All relevant changes are committed (nothing important left unstaged)
- [ ] Commit messages are clear and descriptive
- [ ] Logical grouping makes sense (can review commit history and understand it)
- [ ] No accidental files committed (secrets, temp files, etc.)

## Branch Management

### Current Branch Commits

This workflow focuses on committing to your **current branch**:

```bash
# Check which branch you're on
git branch

# Commit to current branch
git add .
git commit -m "feat: add new feature"
```

### Branch Status

After committing, your current branch has new commits:

```bash
# See commit history
git log --oneline -5

# See branch status relative to remote
git status
```

**Note**: This workflow does NOT cover:
- Pushing to remote
- Creating new branches
- Merging branches
- Pull requests

Those are separate workflows. This focuses only on committing to the current branch and achieving clean working directory status.

## Troubleshooting

### Issue: "nothing to commit" but files are modified

**Cause**: Files might be in .gitignore

```bash
# Check if file is ignored
git check-ignore -v path/to/file

# If it should be tracked, remove from .gitignore
```

### Issue: Commit message editor opens

**Cause**: Ran `git commit` without `-m` flag

**Solution**: 
- Type message in editor, save, and close
- Or cancel with `:q!` (vim) and retry with `-m`

### Issue: "working tree clean" but changes exist

**Cause**: Changes might be unstaged

```bash
# See all changes including unstaged
git status

# See actual differences
git diff
```

## Integration with Task Completion

This workflow is **Step 3** of `task_completion.md`:

```
Task Completion Flow:
1. Update Memory Bank
2. Update README
3. Clear Git Status (← This workflow)
```

Execute as the final step to ensure:
- All documentation is committed
- All code changes are committed
- Project is ready for next session

## Best Practices Summary

### Do ✅
- **Commit frequently** - Don't let changes accumulate
- **Write clear messages** - Future you will thank you
- **Group logically** - Related changes together
- **Review before committing** - Check what you're staging
- **Verify clean status** - Always confirm at the end

### Don't ❌
- **Commit everything blindly** - Review changes first
- **Use vague messages** - "updates" tells nothing
- **Mix unrelated changes** - Keep commits focused
- **Commit secrets** - Check for API keys, passwords
- **Skip verification** - Always confirm clean status

---

**Related Workflows**: `task_completion.md`, `memory_bank_update.md`
**Related Rules**: `.clinerules/version_control.md`
