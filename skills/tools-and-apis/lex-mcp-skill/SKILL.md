---
name: lex-mcp
description: Using the Lex MCP tool to find and verify legislative references for PolicyEngine parameters
---

# Lex MCP Skill

The Lex MCP (Model Context Protocol) tool provides access to legislative and regulatory documents to find authoritative references for PolicyEngine parameters.

## For Contributors

### What is Lex MCP?

Lex MCP is an MCP server that provides access to:
- United States Code (USC)
- Code of Federal Regulations (CFR)
- State statutes and administrative codes
- Federal agency guidance documents

It's used when adding legislative references to PolicyEngine parameters and variables.

### When to Use Lex MCP

Use Lex MCP when:
- Adding new parameters that need references
- Validating existing parameter references
- Finding specific statutory or regulatory citations
- Verifying that references corroborate parameter values

### How to Use Lex MCP

**Check if Lex MCP is available:**
```bash
# List available MCP servers
# (Check Claude Code's MCP configuration)
```

**Typical workflow:**

1. **Identify what you need to reference:**
   - Federal statute? (e.g., 42 USC 8624 - LIHEAP)
   - Federal regulation? (e.g., 7 CFR 273.9 - SNAP income eligibility)
   - State statute? (e.g., Idaho Code 56-1010)

2. **Use Lex MCP to fetch the document:**
   - Search by citation number
   - Browse by topic area
   - Verify effective dates

3. **Extract the specific citation:**
   - Find the exact section/subsection
   - Copy the relevant text
   - Note the section number and any page references

4. **Format as parameter reference:**
   ```yaml
   metadata:
     reference:
       - title: 42 USC 8624(b)(2)(B) - LIHEAP income eligibility ceiling
         href: https://www.law.cornell.edu/uscode/text/42/8624
   ```

### Integration with Reference Validation

Lex MCP helps ensure references meet validation requirements from `reference-validator` agent:

**Reference Completeness:**
- Use Lex MCP to find the authoritative source
- Get the exact section citation
- Obtain the direct link to the statute/regulation

**Reference-Value Corroboration:**
- Read the actual statutory text via Lex MCP
- Verify the text explicitly states the parameter value
- Include the specific quote in the reference title

**Example - Finding LIHEAP Income Limit:**

```yaml
# Parameter: Idaho LIHEAP income limit
description: Idaho limits gross income to this percentage under the Low Income Home Energy Assistance Program.
values:
  2024-01-01: 1.5  # 150% FPL

# Step 1: Use Lex MCP to fetch 42 USC 8624
# Step 2: Find subsection (b)(2)(B)
# Step 3: Verify it mentions "150 percent" or allows states to set this
# Step 4: Also fetch Idaho state plan via WebFetch
# Step 5: Combine federal + state references

metadata:
  reference:
    - title: 42 USC 8624(b)(2)(B) - States may set income eligibility up to 150% of poverty line or 60% of state median income
      href: https://www.law.cornell.edu/uscode/text/42/8624
    - title: Idaho LIHEAP State Plan FY2024, Section 2.3 - "Income eligibility set at 150% of Federal Poverty Level"
      href: https://healthandwelfare.idaho.gov/sites/default/files/liheap-state-plan-2024.pdf
```

### Common Lex MCP Use Cases

**1. Federal Program Parameters:**
- SNAP (7 CFR Part 273)
- TANF (42 USC 601-619, 45 CFR Part 260-265)
- Medicaid (42 USC 1396, 42 CFR Part 430-456)
- EITC (26 USC 32)
- CTC (26 USC 24)

**2. Federal Guidelines Referenced by States:**
- Federal Poverty Guidelines (42 USC 9902)
- Area Median Income (24 CFR Part 5)
- Fair Market Rent (24 CFR Part 888)

**3. State Statutes:**
- State administrative codes
- State public assistance laws
- State tax codes

### Best Practices

**DO:**
- Verify effective dates match parameter dates
- Include subsection details in citations
- Cross-reference federal and state sources
- Test links to ensure they work

**DON'T:**
- Rely solely on secondary sources (like Wikipedia)
- Use generic references without specific sections
- Skip verification that text matches parameter value
- Reference documents you haven't actually read

### Example Workflow: Adding References to Idaho LIHEAP

```bash
# 1. Find parameters without references
grep -r "description:" parameters/gov/states/id/liheap/ | grep -v "reference:"

# 2. For each parameter, use Lex MCP to find:
#    - Federal LIHEAP statute (42 USC 8624)
#    - Idaho state LIHEAP plan
#    - Idaho administrative code (if applicable)

# 3. Read the documents to verify values

# 4. Add references to parameters:
#    - Include exact citations
#    - Quote relevant text in title
#    - Provide direct links

# 5. Validate with reference-validator agent
```

### Integration Points

**Works with agents:**
- `reference-validator` - Ensures references meet quality standards
- `parameter-architect` - Adds references when creating parameters
- `document-collector` - Gathers source documents before using Lex MCP
- `program-reviewer` - Reviews regulatory compliance using references

**Works with skills:**
- `policyengine-parameter-patterns` - Reference format requirements
- `policyengine-standards` - Documentation standards

### Troubleshooting

**Problem:** Lex MCP doesn't have the document
- Solution: Use WebFetch for state-specific documents
- Solution: Check state agency websites directly
- Solution: Document in reference title that statute was verified manually

**Problem:** Effective dates don't match
- Solution: Look for amendments and prior versions
- Solution: Check Federal Register for implementation dates
- Solution: Review state session laws for enactment dates

**Problem:** Reference doesn't explicitly state the value
- Solution: Look for related sections that define calculations
- Solution: Check implementing regulations (CFR) not just statute (USC)
- Solution: Review state administrative code for detailed rules

### Related Resources

**Federal Law Sources:**
- United States Code: https://www.law.cornell.edu/uscode
- Code of Federal Regulations: https://www.ecfr.gov
- Federal Register: https://www.federalregister.gov

**State Law Sources:**
- Check each state's legislative website
- Look for administrative code divisions
- Review agency policy manuals

**PolicyEngine Standards:**
- See `reference-validator` agent for validation requirements
- See `policyengine-parameter-patterns` for reference formatting
- See `/review-pr` command which includes reference validation
