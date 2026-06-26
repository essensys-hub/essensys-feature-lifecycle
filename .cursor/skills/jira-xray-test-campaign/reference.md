# Reference - Jira/Xray Test Campaign

## 1. Environment conventions

Prefer a local `.env` (never committed):

```dotenv
# Jira / Atlassian Cloud
account=service-account@<your-org>.com
token=atlassian-scoped-token
cloudId=your-cloud-id

# Xray Cloud
XRAY_BASE_URL=https://eu.xray.cloud.getxray.app
XRAY_CLIENT_ID=your-xray-client-id
XRAY_CLIENT_SECRET=your-xray-client-secret
```

For Jira auth and gateway URL patterns, follow the `jira-confluence-api` skill.

## 2. Recommended campaign mapping

For most teams, use this mapping:

- `Campaign` -> `Test Plan`
- `Execution cycle` -> `Test Execution`
- `Functional bucket` -> `Test Set`
- `Reusable test case` -> `Test`

If the project uses a custom issue type named `Campaign`, `Validation Campaign`, or similar, verify that first instead of forcing `Test Plan`.

## 3. Jira discovery checklist

Before creating anything, inspect:

- project key
- issue type names
- required fields
- screen constraints
- labels/components/fixVersion conventions

Useful Jira queries:

```text
project = WPMTC ORDER BY updated DESC
project = WPMTC AND issuetype = Test ORDER BY updated DESC
project = WPMTC AND issuetype = "Test Plan" ORDER BY updated DESC
project = WPMTC AND issuetype = "Test Execution" ORDER BY updated DESC
project = WPMTC AND textfields ~ "SITC" ORDER BY updated DESC
```

## 4. Jira REST endpoints

Search issues:

```text
GET /rest/api/3/search?jql=...
```

Get issue:

```text
GET /rest/api/3/issue/{issueKey}
```

Create issue:

```text
POST /rest/api/3/issue
```

Update issue:

```text
PUT /rest/api/3/issue/{issueKey}
```

Always request a minimal field set for reads when possible.

## 5. Xray Cloud auth

Authenticate first:

```bash
curl -sS \
  -H "Content-Type: application/json" \
  -X POST \
  "$XRAY_BASE_URL/api/v2/authenticate" \
  --data "{\"client_id\":\"$XRAY_CLIENT_ID\",\"client_secret\":\"$XRAY_CLIENT_SECRET\"}"
```

The response is a bearer token string valid for a limited duration.

## 6. Xray GraphQL endpoint

All GraphQL requests use:

```text
POST {XRAY_BASE_URL}/api/v2/graphql
Authorization: Bearer <xray-token>
Content-Type: application/json
```

## 7. Common Xray mutations

### Create Test Plan

```graphql
mutation CreatePlan {
  createTestPlan(
    jira: {
      fields: {
        summary: "SITC - Release 1.4.1"
        project: { key: "WPMTC" }
      }
    }
  ) {
    testPlan { issueId jira(fields: ["key"]) }
  }
}
```

### Add Tests to Test Plan

```graphql
mutation AddTests {
  addTestsToTestPlan(
    issueId: "123456"
    testIssueIds: ["111", "222", "333"]
  ) {
    addedTests
    warning
  }
}
```

### Add Test Executions to Test Plan

```graphql
mutation AddExecutions {
  addTestExecutionsToTestPlan(
    issueId: "123456"
    testExecIssueIds: ["444", "555"]
  ) {
    addedTestExecutions
    warning
  }
}
```

## 8. Important note about Test Execution linking

Depending on the Xray Cloud schema/version, adding Tests to a `Test Execution` may be done:

- directly at creation time
- through a dedicated mutation
- or through another Xray-supported path

Do **not** guess the mutation name blindly. Validate the schema or the current docs for your region first if the operation is needed.

## 9. Safe execution pattern

Use this order:

1. search existing campaign assets
2. draft plan of changes
3. ask for confirmation
4. create/update issues
5. link Xray entities
6. verify with JQL + Xray reads

## 10. Verification outputs

After execution, always provide:

- issue keys created
- issue keys reused
- counts of tests linked
- JQL to re-open the campaign quickly
- unresolved gaps

Recommended verification JQL:

```text
project = WPMTC AND issuetype = "Test Plan" AND summary ~ "SITC"
project = WPMTC AND issuetype = "Test Execution" AND summary ~ "SITC"
project = WPMTC AND issuetype = Test AND textfields ~ "SITC"
```

## 11. Failure handling

- `401/403` -> verify auth mode, token scopes, site permissions
- `404` -> verify issue type name or URL base
- GraphQL validation error -> inspect exact mutation/field names before retrying
- missing required field -> inspect project create screen or existing issue JSON
