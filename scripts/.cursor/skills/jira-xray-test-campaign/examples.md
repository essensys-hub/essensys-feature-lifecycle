# Examples - Jira/Xray Test Campaign

## Example 1 - Reuse existing SITC tests in WPMTC

### User request

```text
Je veux une campagne SITC dans WPMTC pour la release 1.4.1, avec les tests deja existants.
```

### Expected approach

1. Search existing tests:

```text
project = WPMTC AND issuetype = Test AND textfields ~ "SITC"
```

2. Search existing campaign objects:

```text
project = WPMTC AND issuetype = "Test Plan" AND summary ~ "SITC"
project = WPMTC AND issuetype = "Test Execution" AND summary ~ "SITC"
```

3. Return a preview before creation:

```markdown
## Campaign Proposal

**Project:** WPMTC
**Campaign label:** SITC

### Reused tests
- WPMTC-5774
- WPMTC-5801
- WPMTC-5802

### To create
- Test Plan: `SITC - Release 1.4.1`
- Test Execution: `SITC - Release 1.4.1 - INT`

### Confirmation needed
- create 1 Test Plan
- create 1 Test Execution
- link 3 existing Tests
```

## Example 2 - Create a campaign with new tests

### User request

```text
Prepare une campagne Xray pour SITC avec 5 nouveaux tests fonctionnels et 2 executions (INT et UAT).
```

### Expected summary

```markdown
## Campaign Summary

**Project:** WPMTC
**Campaign key:** SITC

### Created
- Test Plan: WPMTC-900
- Test Execution INT: WPMTC-901
- Test Execution UAT: WPMTC-902
- Tests: WPMTC-903, WPMTC-904, WPMTC-905, WPMTC-906, WPMTC-907

### Linked
- 5 Tests added to Test Plan
- 2 Test Executions added to Test Plan

### Verification JQL
- `project = WPMTC AND issue in (WPMTC-900, WPMTC-901, WPMTC-902, WPMTC-903, WPMTC-904, WPMTC-905, WPMTC-906, WPMTC-907)`
```

## Example 3 - Minimal GraphQL body for Test Plan

```json
{
  "query": "mutation CreatePlan { createTestPlan(jira: { fields: { summary: \"SITC - Release 1.4.1\", project: { key: \"WPMTC\" } } }) { testPlan { issueId } } }"
}
```

## Example 4 - Safe final response format

```markdown
## Campaign Summary

**Project:** WPMTC
**Campaign key:** SITC

### Created
- Test Plan: WPMTC-123
- Test Execution: WPMTC-124

### Reused
- Tests: WPMTC-5774, WPMTC-5778

### JQL checks
- `project = WPMTC AND issue = WPMTC-123`
- `project = WPMTC AND issuetype = Test AND textfields ~ "SITC"`

### Remaining actions
- set assignee on WPMTC-124
- confirm fixVersion for release 1.4.1
```
