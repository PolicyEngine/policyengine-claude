# Agent Skills Audit - encode-policy Workflow

## Summary
After thorough review of the encode-policy workflow, I've identified that several critical agents are missing skill references that would significantly improve their effectiveness.

## Agents With Correct Skills ✅

### 1. test-creator
**Current Skills:**
- policyengine-testing-patterns-skill ✅
- policyengine-period-patterns-skill ✅
- policyengine-aggregation-skill ✅
**Assessment:** CORRECT - Has all needed skills for test creation

### 2. rules-engineer
**Current Skills:**
- policyengine-implementation-patterns-skill ✅
- policyengine-parameter-patterns-skill ✅
- policyengine-vectorization-skill ✅
- policyengine-aggregation-skill ✅
- policyengine-period-patterns-skill ✅
- policyengine-code-style-skill ✅
**Assessment:** CORRECT - Comprehensive skill set for implementation

### 3. rules-reviewer
**Current Skills:**
- policyengine-review-patterns-skill ✅
- policyengine-vectorization-skill ✅
- policyengine-parameter-patterns-skill ✅
- policyengine-testing-patterns-skill ✅
- policyengine-code-style-skill ✅
**Assessment:** CORRECT - Well-equipped for code review

### 4. ci-fixer
**Current Skills:**
- policyengine-testing-patterns-skill ✅
- policyengine-implementation-patterns-skill ✅
- policyengine-vectorization-skill ✅
- policyengine-code-style-skill ✅
- policyengine-period-patterns-skill ✅
**Assessment:** CORRECT - Has skills needed for fixing issues

### 5. parameter-architect
**Current Skills:**
- policyengine-parameter-patterns-skill ✅
- policyengine-implementation-patterns-skill ✅
**Assessment:** CORRECT - Appropriate for parameter creation

---

## Agents MISSING Skills ❌

### 1. tanf-program-reviewer
**Current Skills:** NONE
**Should Have:**
- policyengine-review-patterns-skill (review procedures)
- policyengine-testing-patterns-skill (test validation)
- policyengine-implementation-patterns-skill (TANF patterns)
- policyengine-parameter-patterns-skill (parameter validation)
- policyengine-vectorization-skill (performance checks)
**Impact:** CRITICAL - This is a key validation agent that needs skills

### 2. implementation-validator
**Current Skills:** NONE
**Should Have:**
- policyengine-implementation-patterns-skill (no hard-coding rules)
- policyengine-parameter-patterns-skill (parameter structure)
- policyengine-vectorization-skill (performance validation)
- policyengine-review-patterns-skill (validation checklists)
**Impact:** HIGH - Validation quality depends on these patterns

### 3. integration-agent
**Current Skills:** NONE
**Should Have:**
- policyengine-testing-patterns-skill (understand test structure for fixing)
- policyengine-implementation-patterns-skill (understand variable patterns)
**Impact:** MEDIUM - Would help identify and fix integration issues

### 4. naming-coordinator
**Current Skills:** NONE
**Should Have:**
- policyengine-implementation-patterns-skill (naming conventions)
- policyengine-parameter-patterns-skill (parameter naming)
**Impact:** MEDIUM - Would ensure consistent naming patterns

### 5. document-collector (document_collector.md)
**Current Skills:** NONE
**Could Have:**
- policyengine-implementation-patterns-skill (know what to look for)
- policyengine-parameter-patterns-skill (identify parameter needs)
**Impact:** LOW - Mainly searches and organizes external docs

### 6. cross-program-validator (optional phase)
**Current Skills:** NONE
**Should Have:**
- policyengine-implementation-patterns-skill (cross-program patterns)
- policyengine-review-patterns-skill (validation procedures)
**Impact:** MEDIUM - Important for production implementations

### 7. documentation-enricher (optional phase)
**Current Skills:** NONE
**Could Have:**
- policyengine-implementation-patterns-skill (documentation patterns)
**Impact:** LOW - Enhancement agent

### 8. performance-optimizer (optional phase)
**Current Skills:** NONE
**Should Have:**
- policyengine-vectorization-skill (optimization patterns)
- policyengine-code-style-skill (efficiency patterns)
**Impact:** MEDIUM - Critical for performance work

---

## Agents That DON'T Need Skills ✓

### 1. issue-manager
**Reason:** Pure GitHub operations, no PolicyEngine-specific knowledge needed

### 2. pr-pusher
**Reason:** Formatting and CI operations, no domain knowledge required

---

## Priority Fixes

### CRITICAL (Fix Immediately)
1. **tanf-program-reviewer** - Add 5 skills for proper TANF review
2. **implementation-validator** - Add 4 skills for validation

### HIGH (Fix Soon)
3. **performance-optimizer** - Add vectorization and code-style skills
4. **integration-agent** - Add testing and implementation skills

### MEDIUM (Consider)
5. **naming-coordinator** - Add implementation and parameter skills
6. **cross-program-validator** - Add implementation and review skills

### LOW (Optional)
7. **document-collector** - Could add skills but not essential
8. **documentation-enricher** - Enhancement only

---

## Recommended Actions

### 1. Update tanf-program-reviewer.md
Add after line 10:
```markdown
## Skills Used

- **policyengine-review-patterns-skill** - Review procedures and checklists
- **policyengine-testing-patterns-skill** - Test structure validation
- **policyengine-implementation-patterns-skill** - TANF implementation patterns
- **policyengine-parameter-patterns-skill** - Parameter structure validation
- **policyengine-vectorization-skill** - Performance and vectorization checks
```

### 2. Update implementation-validator.md
Add after line 11:
```markdown
## Skills Used

- **policyengine-implementation-patterns-skill** - No hard-coding principles
- **policyengine-parameter-patterns-skill** - Parameter organization rules
- **policyengine-vectorization-skill** - Vectorization requirements
- **policyengine-review-patterns-skill** - Validation checklists
```

### 3. Update performance-optimizer.md
Add skills section with:
- **policyengine-vectorization-skill** - Core optimization patterns
- **policyengine-code-style-skill** - Efficiency patterns

### 4. Update integration-agent.md
Add skills section with:
- **policyengine-testing-patterns-skill** - Test structure for fixes
- **policyengine-implementation-patterns-skill** - Variable patterns

---

## Impact Analysis

**Current State Risk:**
- Key validation agents lack access to critical knowledge
- Particularly concerning for tanf-program-reviewer which is used in Phase 7
- implementation-validator in Phase 7 can't properly validate without skills

**After Fixes:**
- All agents in the encode-policy workflow will have appropriate skills
- Better consistency and quality in implementation
- Reduced errors and rework

---

## Verification Steps

After adding skills to agents:
1. Ensure skills are listed in marketplace.json for the complete plugin
2. Test that agents can access the skills during execution
3. Monitor for improved validation quality

---

*This audit reveals that while the core development agents (test-creator, rules-engineer) have proper skills, the validation and review agents are significantly under-equipped.*