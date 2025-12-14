# Task Completion Workflow

**⚠️ CRITICAL: This workflow MUST be executed sequentially. DO NOT skip any steps. Each step MUST be completed before proceeding to the next step.**

This workflow should be executed each time a task is completed.

---

## MANDATORY SEQUENTIAL WORKFLOW

### Step 1: Review ALL Memory Bank Files (MANDATORY - READ ONLY)

**YOU MUST READ EVERY FILE BEFORE ANY UPDATES. NO EXCEPTIONS.**

Use `read_file` tool on EACH of the following files individually:

**REQUIRED READING CHECKLIST (Complete ALL before proceeding to Step 2):**
- [ ] `memorybank/projectbrief.md` - Foundation and scope
- [ ] `memorybank/productContext.md` - Product goals and user experience  
- [ ] `memorybank/systemPatterns.md` - Architecture and design patterns
- [ ] `memorybank/techContext.md` - Technologies and setup
- [ ] `memorybank/activeContext.md` - Current work and recent changes
- [ ] `memorybank/progress.md` - Status and what's next
- [ ] Any additional context files in memorybank/

**WHY THIS MATTERS:** You cannot determine what needs updating without reading everything first. Every file provides crucial context.

**STOP HERE** until ALL files above have been read. Do NOT proceed to Step 2 until this is complete.

---

### Step 2: Update Memory Bank Files (ONE BY ONE)

**ONLY AFTER completing Step 1**, update memory bank files one by one as needed:

**Update Priority Order:**
1. **FIRST: Update `activeContext.md`** with:
   - Recent changes made during this task
   - Current work focus
   - Next steps
   - Any new patterns or insights discovered
   
2. **SECOND: Update `progress.md`** with:
   - What was accomplished in this task
   - What's now working
   - What remains to be done
   - Any new known issues

3. **THEN: Update other files ONLY IF NEEDED:**
   - `projectbrief.md` - if core requirements, scope, or goals evolved
   - `systemPatterns.md` - if architecture or patterns changed
   - `techContext.md` - if technologies or setup changed
   - `productContext.md` - if requirements or understanding evolved

**UPDATE RULES:**
- Update files ONE AT A TIME using `replace_in_file` or `write_to_file`
- Complete each file update before moving to the next
- Document rationale for significant changes
- Do NOT skip files that need updates

**See detailed workflow**: `.clinerules/workflows/memory_bank_update.md`

**CHECKPOINT:** Verify all necessary memory bank updates are complete before proceeding to Step 3.

---

### Step 3: Update README.md

**ONLY AFTER completing Step 2**, update README.md to synchronize with current project state:

**Required Actions:**
1. **READ `README.md`** using `read_file` tool first
2. **REVIEW** alignment with memory bank (especially progress.md)
3. **UPDATE** the following sections as needed:
   - **Current Status**: Align with progress.md milestones
   - **Setup/Installation**: Keep steps accurate and tested
   - **Usage**: Update commands and examples
   - **Project Structure**: Reflect actual file organization

**UPDATE RULES:**
- Make updates using `replace_in_file` tool
- Keep README concise and user-focused (detailed docs belong elsewhere)
- Test any commands or examples before documenting them
- Update only sections that need changes

**See detailed workflow**: `.clinerules/workflows/readme_update.md`

**CHECKPOINT:** Verify README.md is updated and accurate before proceeding to Step 4.

---

### Step 4: Clear Git Status (FINAL STEP)

**ONLY AFTER completing Steps 1, 2, and 3**, clean up the git working directory:

**Execute the following commands in sequence:**

1. **Stage all changes:**
   ```bash
   git add .
   ```

2. **Review staged changes:**
   ```bash
   git status
   ```

3. **Commit with descriptive message:**
   ```bash
   git commit -m "task: [describe what changed and why]"
   ```
   
   **Commit Message Guidelines:**
   - Be specific about what was accomplished
   - Explain why changes were made
   - Reference task or feature name if applicable
   - Example: "task: implement bot evaluation framework with tournament simulation"

4. **Verify clean status:**
   ```bash
   git status
   ```
   
   **Expected output:** "nothing to commit, working tree clean"

**See detailed workflow**: `.clinerules/workflows/git_status_clear.md`

**FINAL CHECKPOINT:** Verify git status is clean and all changes are committed.

---

## Critical Execution Rules

**🚫 DO NOT:**
- Skip any steps in this workflow
- Update memory bank files without reading them first
- Update multiple steps simultaneously
- Proceed to next step before completing current step
- Commit before updating memory bank and README

**✅ DO:**
- Execute steps in exact sequential order (1 → 2 → 3 → 4)
- Complete ALL required reading in Step 1 before any updates
- Update files one by one in Step 2
- Verify completion at each checkpoint
- Use descriptive, clear commit messages

---

## Workflow Completion Checklist

Use this checklist to track workflow completion:

- [ ] Step 1: Read ALL memory bank files (all 6+ core files)
- [ ] Step 2: Updated memory bank files one by one as needed
- [ ] Step 3: Updated README.md to reflect current state
- [ ] Step 4: Executed git commands and verified clean status

**Only mark this workflow as complete when ALL checkboxes above are checked.**

---

**Workflow Trigger**: Execute this workflow when you see task completion or when explicitly requested by the user.

**REMINDER**: This workflow ensures continuity between sessions. Your memory resets completely, and these files are your ONLY connection to previous work. Complete every step thoroughly.
