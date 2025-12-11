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

### Step 1: Review ALL Files

Start by reading every memory bank file to understand current state:

- [ ] `projectbrief.md` - Foundation document
- [ ] `productContext.md` - Product understanding  
- [ ] `systemPatterns.md` - Architecture patterns
- [ ] `techContext.md` - Technical setup
- [ ] `activeContext.md` - Current context
- [ ] `progress.md` - Current status

**Critical**: When user says **update memory bank**, you MUST review ALL files, even if some don't need updates.

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

When user explicitly requests a memory bank update:

1. **Read ALL six core files** - Even if some seem up-to-date
2. **Focus particularly on**:
   - `activeContext.md` - Most likely to need updates
   - `progress.md` - Track recent accomplishments
3. **Look for gaps**:
   - Recent work not documented
   - Stale information that's changed
   - Missing context about decisions
4. **Update comprehensively**: Don't just update one file
5. **Verify consistency**: Ensure files tell a coherent story

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
