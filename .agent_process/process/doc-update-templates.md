# Documentation Update Templates

Quick copy-paste templates for common documentation updates. Organized by audience and type.

**Remember**: Use these as starting points. Customize for your specific project's documentation standards.

---

## End User Documentation Templates

### How-To Guide Template (Task-Oriented)

```markdown
# How to [Accomplish Specific Task]

**What you'll accomplish**: [One sentence describing the outcome]

**Prerequisites**:
- [Requirement 1]
- [Requirement 2]

**Estimated time**: [X minutes]

---

## Steps

### 1. [First Major Step]

[Brief explanation of what this step accomplishes]

**In the application**:
1. Navigate to [location]
2. Click [button/option]
3. [Action]

**Expected result**: [What the user should see]

### 2. [Second Major Step]

[Continue pattern...]

---

## Troubleshooting

**Problem**: [Common issue]
**Solution**: [How to fix it]

**Problem**: [Another common issue]
**Solution**: [How to fix it]

---

## Related Guides
- [Link to related how-to]
- [Link to reference docs]
```

### Tutorial Template (Learning-Oriented)

```markdown
# Tutorial: Your First [Feature/Workflow]

**What you'll learn**:
- [Learning objective 1]
- [Learning objective 2]
- [Learning objective 3]

**What you'll build**: [Concrete outcome]

**Time required**: [X minutes]

**Prerequisites**:
- [Prerequisite knowledge/setup]

---

## Introduction

[Brief context about what this feature does and why it's useful]

**By the end of this tutorial**, you'll have [concrete achievement].

---

## Step 1: [Foundational Concept]

Let's start by [doing something simple].

[Hands-on instruction with explanation]

**What just happened?** [Brief explanation of the concept]

---

## Step 2: [Build on Previous Step]

Now that you understand [concept], let's [next step].

[Continue pattern - always explain WHY, not just WHAT]

---

## Step 3: [Complete the Feature]

[Final step to working feature]

**Congratulations!** You've just [achievement].

---

## Next Steps

Now that you've learned [basics], you can:
- [Advanced topic 1] - See [link]
- [Advanced topic 2] - See [link]
- [Related feature] - See [link]

---

## What You Learned

- ✅ [Concept 1]
- ✅ [Concept 2]
- ✅ [Concept 3]
```

### User Reference Template (Information-Oriented)

```markdown
# [Feature Name] Reference

**Overview**: [One-sentence description of the feature]

**Available in**: [Version/plan/tier]

---

## Feature Options

### Option 1: [Name]

**Description**: [What this option does]

**When to use**: [Use case]

**How to access**: [UI path or location]

**Settings**:
- **[Setting name]**: [Description] (Default: [value])
- **[Setting name]**: [Description] (Default: [value])

### Option 2: [Name]

[Repeat pattern...]

---

## Keyboard Shortcuts

| Action | Windows/Linux | Mac |
|--------|---------------|-----|
| [Action] | `Ctrl+K` | `Cmd+K` |
| [Action] | `Ctrl+Shift+P` | `Cmd+Shift+P` |

---

## Limits and Constraints

- **Maximum [X]**: [Value]
- **[Constraint]**: [Description]

---

## Related Features
- [Link to related feature]
- [Link to tutorial]
```

---

## Developer Documentation Templates

### API Reference Template (Information-Oriented)

```markdown
## [Endpoint/Function Name]

**Added in**: [Version/Date]

**Description**: [One-sentence summary of what this does]

---

### Endpoint Details

**Method**: `GET` | `POST` | `PUT` | `DELETE`
**Path**: `/api/v1/resource/{id}`

**Authentication**: Required | Optional | None

---

### Request

**Path Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `id` | string | Yes | [Description] |

**Query Parameters**:
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `limit` | integer | No | 20 | [Description] |
| `offset` | integer | No | 0 | [Description] |

**Request Body**:
```json
{
  "field1": "string",
  "field2": 123,
  "nested": {
    "field3": true
  }
}
```

**Field Descriptions**:
- `field1` (string, required): [Description]
- `field2` (integer, optional): [Description]
- `nested.field3` (boolean, required): [Description]

---

### Response

**Success Response** (`200 OK`):
```json
{
  "id": "abc123",
  "status": "success",
  "data": {
    "result": "value"
  }
}
```

**Error Responses**:

`400 Bad Request` - [When this happens]
```json
{
  "error": "Invalid parameter",
  "details": "field1 must be non-empty"
}
```

`404 Not Found` - [When this happens]
`401 Unauthorized` - [When this happens]

---

### Examples

**cURL**:
```bash
curl -X GET "https://api.example.com/v1/resource/abc123" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

**JavaScript**:
```javascript
const response = await fetch('/api/v1/resource/abc123', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN'
  }
});
const data = await response.json();
```

**Python**:
```python
import requests

response = requests.get(
    'https://api.example.com/v1/resource/abc123',
    headers={'Authorization': 'Bearer YOUR_TOKEN'}
)
data = response.json()
```

---

### Notes

- [Important behavior or edge case]
- [Performance consideration]
- [Common pitfall]

---

### See Also
- [Related endpoint]
- [Integration guide]
```

### Function/Class Reference Template

```markdown
## `functionName(param1, param2)`

**Module**: `module.submodule`
**Added in**: [Version]

**Description**: [What this function does and when to use it]

---

### Signature

```typescript
function functionName(
  param1: string,
  param2: number,
  options?: Options
): Promise<Result>
```

### Parameters

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `param1` | `string` | Yes | - | [Description] |
| `param2` | `number` | Yes | - | [Description] |
| `options` | `Options` | No | `{}` | [Description] |

**Options Object**:
```typescript
interface Options {
  timeout?: number;  // Default: 5000
  retries?: number;  // Default: 3
}
```

### Returns

**Type**: `Promise<Result>`

```typescript
interface Result {
  success: boolean;
  data?: any;
  error?: string;
}
```

**Resolves with**: [Description of success case]
**Rejects with**: [Description of error cases]

---

### Examples

**Basic Usage**:
```typescript
const result = await functionName('value', 42);
if (result.success) {
  console.log(result.data);
}
```

**With Options**:
```typescript
const result = await functionName('value', 42, {
  timeout: 10000,
  retries: 5
});
```

**Error Handling**:
```typescript
try {
  const result = await functionName('value', 42);
} catch (error) {
  console.error('Operation failed:', error.message);
}
```

---

### Throws

- `ValidationError` - When [condition]
- `TimeoutError` - When [condition]

---

### Notes

- [Performance characteristics]
- [Thread safety considerations]
- [Common pitfalls]

---

### See Also
- [`relatedFunction()`](#relatedFunction) - [Relationship]
- [Integration Guide](link) - [Context]
```

### Architecture Explanation Template (Understanding-Oriented)

```markdown
# Architecture Decision: [Decision Name]

**Status**: Accepted | Proposed | Deprecated
**Date**: [YYYY-MM-DD]
**Decision makers**: [Who made this decision]

---

## Context

[What is the issue that we're seeing that is motivating this decision or change?]

**Current situation**:
- [Existing system/approach]
- [Pain points or limitations]
- [What triggered this decision]

---

## Decision

We will [decision statement].

**Key changes**:
- [Major change 1]
- [Major change 2]
- [Major change 3]

---

## Rationale

### Why This Approach

[Explain the reasoning behind the decision]

**Benefits**:
- ✅ [Benefit 1]
- ✅ [Benefit 2]
- ✅ [Benefit 3]

**Trade-offs**:
- ⚠️ [Trade-off 1] - We accept this because [reason]
- ⚠️ [Trade-off 2] - We accept this because [reason]

---

## Alternatives Considered

### Alternative 1: [Name]

**Approach**: [Brief description]

**Rejected because**: [Reason]

### Alternative 2: [Name]

**Approach**: [Brief description]

**Rejected because**: [Reason]

---

## Consequences

### Positive
- [Positive consequence 1]
- [Positive consequence 2]

### Negative
- [Negative consequence 1] - [Mitigation strategy]
- [Negative consequence 2] - [Mitigation strategy]

### Neutral
- [Change that is neither good nor bad, just different]

---

## Implementation Notes

**Migration path**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Dependencies**:
- [Dependency 1]
- [Dependency 2]

**Risks**:
- [Risk 1] - [Mitigation]
- [Risk 2] - [Mitigation]

---

## Related Decisions
- [Link to related architecture decision]
- [Link to related design document]

---

## References
- [External resource]
- [Research paper]
- [Benchmark results]
```

### Migration Guide Template (Task-Oriented for Developers)

```markdown
# Migrating from [Old System] to [New System]

**Migration difficulty**: Low | Medium | High
**Estimated time**: [Time estimate for typical project]
**Breaking changes**: Yes | No

---

## Overview

**What's changing**: [Brief summary]

**Why this change**: [Rationale in 1-2 sentences]

**Timeline**:
- [Old system] deprecated as of: [Date]
- [Old system] will be removed in: [Version/Date]

---

## Quick Migration (Most Common Case)

For most projects, migration is straightforward:

### Before
```typescript
// Old approach
import { OldClass } from 'old-module';

const instance = new OldClass(config);
instance.doSomething();
```

### After
```typescript
// New approach
import { NewClass } from 'new-module';

const instance = new NewClass(config);
instance.doSomething();
```

**Key changes**:
- Import path changed: `old-module` → `new-module`
- Class renamed: `OldClass` → `NewClass`
- Method signatures unchanged ✅

---

## Detailed Migration Steps

### Step 1: Update Dependencies

```bash
npm install new-package@latest
npm uninstall old-package
```

### Step 2: Update Imports

**Find and replace** across your codebase:
- `import { OldClass }` → `import { NewClass }`
- `from 'old-module'` → `from 'new-module'`

### Step 3: Update Configuration

**Old config**:
```json
{
  "oldKey": "value",
  "legacyOption": true
}
```

**New config**:
```json
{
  "newKey": "value",
  "modernOption": true
}
```

**Mapping**:
- `oldKey` → `newKey` (direct rename)
- `legacyOption` → `modernOption` (direct rename)

### Step 4: Update Method Calls (If Changed)

| Old Method | New Method | Notes |
|------------|------------|-------|
| `oldMethod()` | `newMethod()` | Direct rename |
| `deprecatedMethod(x)` | `betterMethod(x)` | Same signature |
| `removedMethod()` | Use `alternative()` | Different approach needed |

---

## Edge Cases and Complex Scenarios

### Scenario 1: [Complex Migration Case]

**If you were using**: [Old pattern]

**Migrate to**: [New pattern]

**Example**:
```typescript
// Before
[old code]

// After
[new code]
```

### Scenario 2: [Another Complex Case]

[Repeat pattern...]

---

## Breaking Changes

### Change 1: [Breaking Change Description]

**What changed**: [Description]

**Impact**: [Who is affected]

**Migration**:
```typescript
// Old code (will break)
const result = oldWay();

// New code (correct)
const result = newWay();
```

### Change 2: [Another Breaking Change]

[Repeat pattern...]

---

## Troubleshooting

### Error: "[Common Error Message]"

**Cause**: [Why this happens]

**Solution**:
```typescript
// Fix
[corrected code]
```

### Error: "[Another Common Error]"

**Cause**: [Why this happens]

**Solution**: [How to fix]

---

## Backward Compatibility

**Can old and new coexist?** [Yes/No]

**If yes**:
- You can migrate incrementally
- Both systems will work during transition
- Recommended: [Migration strategy]

**If no**:
- You must migrate all at once
- Recommended: [Migration strategy]
- Test thoroughly before deploying

---

## Testing Your Migration

```typescript
// Test that verifies migration worked
import { NewClass } from 'new-module';

describe('Migration to NewClass', () => {
  it('should work with new implementation', () => {
    const instance = new NewClass(config);
    expect(instance.doSomething()).toBe(expectedResult);
  });
});
```

---

## Need Help?

- [Link to detailed API docs]
- [Link to GitHub discussions]
- [Link to migration support issue]

**Common pitfalls**:
- [Pitfall 1 and how to avoid]
- [Pitfall 2 and how to avoid]
```

### Integration Guide Template (Task-Oriented for Developers)

```markdown
# Integrating [Library/System Name]

**Difficulty**: Beginner | Intermediate | Advanced
**Time to integrate**: [Estimate]

---

## Prerequisites

**Required**:
- [Requirement 1] (version X.Y or higher)
- [Requirement 2]

**Optional** (for advanced features):
- [Optional requirement]

**Assumed knowledge**:
- [Skill/concept 1]
- [Skill/concept 2]

---

## Installation

### Using npm
```bash
npm install library-name
```

### Using yarn
```bash
yarn add library-name
```

### Using pnpm
```bash
pnpm add library-name
```

---

## Basic Setup

### 1. Initialize the Library

```typescript
import { Library } from 'library-name';

const lib = new Library({
  apiKey: process.env.API_KEY,
  environment: 'production'
});
```

### 2. Configure (Optional)

```typescript
lib.configure({
  timeout: 5000,
  retries: 3,
  logLevel: 'info'
});
```

### 3. Basic Usage

```typescript
// Most common use case
const result = await lib.doSomething({
  param: 'value'
});

console.log(result);
```

**Expected output**:
```json
{
  "status": "success",
  "data": {...}
}
```

---

## Common Integration Patterns

### Pattern 1: [Common Use Case]

**When to use**: [Scenario]

```typescript
// Implementation
[code example]
```

**Explanation**: [Why this pattern works]

### Pattern 2: [Another Common Use Case]

[Repeat pattern...]

---

## Framework-Specific Integration

### React
```typescript
import { useLibrary } from 'library-name/react';

function MyComponent() {
  const { data, loading, error } = useLibrary({
    param: 'value'
  });

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return <div>{data}</div>;
}
```

### Next.js
```typescript
// pages/api/example.ts
import { Library } from 'library-name';

export default async function handler(req, res) {
  const lib = new Library({ apiKey: process.env.API_KEY });
  const result = await lib.doSomething(req.body);
  res.json(result);
}
```

### Express
```typescript
import express from 'express';
import { Library } from 'library-name';

const app = express();
const lib = new Library({ apiKey: process.env.API_KEY });

app.post('/api/endpoint', async (req, res) => {
  const result = await lib.doSomething(req.body);
  res.json(result);
});
```

---

## Configuration Reference

```typescript
interface LibraryConfig {
  apiKey: string;          // Required: Your API key
  environment?: string;    // Default: 'production'
  timeout?: number;        // Default: 5000ms
  retries?: number;        // Default: 3
  logLevel?: LogLevel;     // Default: 'info'
}
```

**Environment variables**:
```bash
API_KEY=your_key_here
LIBRARY_TIMEOUT=10000
LIBRARY_LOG_LEVEL=debug
```

---

## Error Handling

```typescript
try {
  const result = await lib.doSomething(params);
} catch (error) {
  if (error instanceof ValidationError) {
    // Handle validation errors
    console.error('Invalid input:', error.message);
  } else if (error instanceof TimeoutError) {
    // Handle timeouts
    console.error('Request timed out');
  } else {
    // Handle other errors
    console.error('Unexpected error:', error);
  }
}
```

---

## Best Practices

- ✅ **Do**: [Best practice 1]
- ✅ **Do**: [Best practice 2]
- ❌ **Don't**: [Anti-pattern 1]
- ❌ **Don't**: [Anti-pattern 2]

---

## Troubleshooting

### Issue: [Common Problem]

**Symptoms**: [How you know this is the problem]

**Solution**: [How to fix]

### Issue: [Another Common Problem]

[Repeat pattern...]

---

## Next Steps

Now that you have basic integration working:
1. [Advanced feature 1] - See [link]
2. [Advanced feature 2] - See [link]
3. [Deployment guide] - See [link]

---

## Complete Example

See [examples/complete-integration/](link) for a fully working example project.

---

## Support

- 📖 [Full API Reference](link)
- 💬 [GitHub Discussions](link)
- 🐛 [Report an Issue](link)
```

---

## README.md Update Template (For Developer Users)

When your change affects installation, setup, or basic usage:

```markdown
## [New Section or Updated Section]

[Updated content that reflects your changes]

### Example: Adding New Installation Requirement

## Installation

**Requirements**:
- Node.js 18+ (updated from 16+)
- Python 3.11+ (NEW - required for [feature])

```bash
# Install dependencies
npm install

# NEW: Set up Python environment for [feature]
pip install -r requirements.txt
```

### Example: Adding New Environment Variable

## Configuration

Create a `.env` file:

```bash
API_KEY=your_key
DATABASE_URL=postgres://...
NEW_FEATURE_ENABLED=true  # NEW: Enables [feature]
```
```

---

## CONTRIBUTING.md Update Template (For Contributors)

When your change affects how people contribute:

```markdown
## [New Section or Updated Section]

### Example: New Code Standard

## Code Standards

[Existing standards...]

### NEW: [Standard Name]

All [type of code] must now [requirement].

**Why**: [Rationale]

**Example**:
```typescript
// ✅ Good
[correct example]

// ❌ Bad
[incorrect example]
```

**Pre-commit hook**: This is automatically enforced by [hook name].
```

---

## Tips for Using These Templates

1. **Start with the template** closest to your documentation type
2. **Delete sections** that don't apply to your specific case
3. **Add sections** if you need additional information
4. **Keep examples** real - use actual code from your project
5. **Update version numbers** and dates
6. **Test code examples** - make sure they actually work
7. **Link liberally** - connect related documentation

**Remember**: These templates are starting points. Adapt them to match your project's documentation standards and style.
