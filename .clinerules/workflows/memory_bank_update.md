# Memory Bank Update Workflow

This workflow ensures the memory bank accurately reflects the current project state. Since Cline's memory resets between sessions, maintaining accurate documentation is critical for continuity.

## When to Update Memory Bank

Trigger this workflow when:

1. **After completing significant tasks** - Major features, bug fixes, architectural changes
2. **Discovering new project patterns** - New insights about how the system works
3. **User explicitly requests** with **update memory bank**
4. **Before task completion** - As part of task_completion.md workflow
5. **Context needs clarification** - When information becomes stale or unclear
6. **Scope or requirements change** - Project direction shifts

## Memory Bank Files Hierarchy

Understanding file relationships helps prioritize updates:

```
projectbrief.md (Foundation - rarely changes)
    ├── productContext.md (User experience & requirements)
    ├── systemPatterns.md (Architecture & technical decisions)
    └── techContext.md (Technologies & setup)
            ↓
    activeContext.md (Current work & recent changes)
            ↓
    progress.md (Status tracking & accomplishments)
```

## Comprehensive Update Process

### Step 1: READ ALL FILES (MANDATORY - NO EXCEPTIONS)

**CRITICAL RULE**: Before making ANY updates, you MUST read EVERY core memory bank file using `read_file`. This is not optional.

**Required Reading Order** (use `read_file` on each):

1. [ ] `projectbrief.md` - Foundation document that shapes everything
2. [ ] `productContext.md` - Product goals and user experience
3. [ ] `systemPatterns.md` - Architecture and design patterns  
4. [ ] `techContext.md` - Technologies and development setup
5. [ ] `activeContext.md` - Current work and recent changes
6. [ ] `progress.md` - Status tracking and accomplishments

**Why ALL Files Matter**:
- Cannot determine what needs updating without reading everything first
- Ensures updates maintain consistency across all documentation
- Prevents losing important context or creating contradictions
- Each file provides essential perspective on the project state

**REMEMBER**: After memory reset, you know NOTHING about the project. You cannot know what needs updating without reading all files first. Skipping files = incomplete understanding = poor updates.

### Step 2: Update Priority Files

Focus on files that track current state (updated most frequently):

#### High Priority: `activeContext.md`
Update with:
- **Recent changes made**: What was just completed or modified
- **Current work focus**: What you're working on now
- **Next steps**: Immediate priorities
- **Active decisions**: Ongoing considerations
- **New patterns discovered**: Important insights about the codebase
- **Learnings**: Key takeaways from recent work

#### High Priority: `progress.md`
Update with:
- **Completed items**: Move from "In Progress" to "Complete"
- **What's now working**: New functionality that's operational
- **Current status**: Overall project state
- **Known issues**: New bugs or blockers discovered
- **What's left to build**: Update remaining work

### Step 3: Update Foundation Files (As Needed)

These files change less frequently but are critical when they do:

#### `projectbrief.md`
**Update when**:
- Core project goals evolve
- Scope changes significantly
- Requirements are refined or expanded
- Success criteria shifts

**Contains**:
- Project purpose and goals
- Core requirements
- Success criteria
- Scope boundaries

#### `productContext.md`
**Update when**:
- User experience understanding deepens
- Problem space clarity improves
- Feature requirements change
- Usage patterns become clearer

**Contains**:
- Why the project exists
- Problems it solves
- How it should work
- User experience goals

#### `systemPatterns.md`
**Update when**:
- Architecture changes
- New design patterns adopted
- Component relationships evolve
- Critical implementation paths discovered

**Contains**:
- System architecture
- Key technical decisions
- Design patterns in use
- Component relationships

#### `techContext.md`
**Update when**:
- New technologies added
- Development setup changes
- Dependencies updated
- Tool usage evolves

**Contains**:
- Technologies and frameworks
- Development environment setup
- Technical constraints
- Dependencies and tools

### Step 4: Ensure Consistency

Cross-check files for alignment:

- [ ] `activeContext.md` next steps match `progress.md` planned items
- [ ] `progress.md` status aligns with `activeContext.md` current focus
- [ ] `systemPatterns.md` reflects actual architecture in codebase
- [ ] `techContext.md` matches actual dependencies and setup
- [ ] `productContext.md` aligns with `projectbrief.md` goals

### Step 5: Document Insights

Capture key learnings:
- **Patterns discovered**: "Found that X approach works better than Y because..."
- **Decisions made**: "Chose to implement Z this way due to..."
- **Context for future**: "Important to know that..."
- **Gotchas**: "Watch out for..."

## Update Guidelines

### Do ✅
- **Be specific**: "Implemented Alpha-Beta pruning for game tree search" not "Added optimization"
- **Explain why**: Include rationale for decisions
- **Keep current**: Focus on present state, not exhaustive history
- **Link concepts**: Show how pieces relate
- **Capture insights**: Document what you learned

### Don't ❌
- **Duplicate information**: If it's in code/comments, don't repeat in memory bank
- **Write novellas**: Keep concise and scannable
- **Include temporary notes**: "TODO: fix this later" belongs in progress.md Known Issues
- **Overcomplicate**: Simple, clear language wins
- **Forget relationships**: Ensure files stay consistent with each other

## Special Case: User Requests "Update Memory Bank"

When user explicitly requests a memory bank update, follow this MANDATORY sequence:

### Phase 1: READ EVERYTHING (No Updates Yet)

**YOU MUST USE `read_file` ON EACH FILE INDIVIDUALLY:**

```
1. read_file("memorybank/projectbrief.md")
2. read_file("memorybank/productContext.md")
3. read_file("memorybank/systemPatterns.md")
4. read_file("memorybank/techContext.md")
5. read_file("memorybank/activeContext.md")
6. read_file("memorybank/progress.md")
```

**DO NOT SKIP ANY FILES** - You cannot know what needs updating without reading everything first.

**DO NOT START UPDATING** until you have read all 6 core files.

### Phase 2: ANALYZE (After Reading All Files)

Now that you've read everything, identify:

- **Recent work not documented** - What changed that isn't captured?
- **Stale information** - What's documented but no longer accurate?
- **Missing context about decisions** - Were important choices made without rationale?
- **Inconsistencies between files** - Do files contradict each other?
- **Gaps in current status** - Is activeContext.md and progress.md current?

### Phase 3: UPDATE (Make Changes)

Only after reading all files and analyzing, update:

1. **activeContext.md** - Most frequently needs updates for current work
2. **progress.md** - Update status and accomplishments
3. **Other files as needed** - Based on analysis from Phase 2

### Phase 4: VERIFY

Ensure:
- [ ] All 6 core files were read before any updates
- [ ] Updates maintain consistency across files
- [ ] Files tell a coherent story together
- [ ] Nothing important was missed

## Verification Checklist

Before completing the update:

- [ ] All recent changes are documented
- [ ] Current work focus is clear
- [ ] Next steps are actionable
- [ ] Files are consistent with each other
- [ ] Key decisions have rationale
- [ ] Important patterns are captured
- [ ] Progress status is accurate
- [ ] Known issues are listed

## Memory Bank Philosophy

Remember: **After every session reset, the memory bank is Cline's ONLY link to the project.**

- Write for "future Cline" who knows nothing about the project
- Prioritize clarity over cleverness
- Document the "why" not just the "what"
- Keep information current and actionable
- Make connections between concepts explicit

## Example Update Flow

```
Scenario: Just completed bot001 verification

1. Read all memory bank files
2. Update activeContext.md:
   - Recent changes: "Completed bot001 verification with test suite"
   - Current focus: "Preparing Botzone deployment"
   - Next steps: "Create deployment script, test submission format"
   - Pattern discovered: "Test harness design works well for isolation"
   
3. Update progress.md:
   - Move "Bot001 verification" to Complete
   - Update status: "Bot ready for deployment"
   - Add to Working: "Bot001 passes all local tests"
   
4. Check other files:
   - systemPatterns.md: No architecture changes
   - techContext.md: No new dependencies
   - productContext.md: Understanding unchanged
   - projectbrief.md: Goals still aligned
   
5. Verify consistency:
   - activeContext next steps align with progress planned items ✓
   - Status indicators consistent across files ✓
```

---

**Related Workflows**: `task_completion.md`, `readme_update.md`
**Related Rules**: `.clinerules/documentation.md`, `.clinerules/memorybank.md`
