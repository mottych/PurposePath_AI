# API Naming Conventions

## JSON Property Naming Standard

**ALL API endpoints use `snake_case` for JSON property names.**

This is enforced in the backend configuration:
- `PurposePath.Shared/Lambda/BaseLambdaFunction.cs` (line 172)
- Uses custom `JsonSnakeCaseNamingPolicy` for consistency with Python services

## Examples

### ✅ CORRECT - snake_case

```json
{
  "business_name": "Purpose Path",
  "website": "https://purposepath.ai",
  "created_at": "2025-10-20T12:00:00Z",
  "is_active": true,
  "user_profile": {
    "first_name": "John",
    "last_name": "Doe",
    "email_verified": true
  }
}
```

### ❌ INCORRECT - camelCase

```json
{
  "businessName": "Purpose Path",
  "website": "https://purposepath.ai",
  "createdAt": "2025-10-20T12:00:00Z",
  "isActive": true,
  "userProfile": {
    "firstName": "John",
    "lastName": "Doe",
    "emailVerified": true
  }
}
```

## C# to JSON Mapping

The backend automatically converts C# `PascalCase` properties to `snake_case` JSON:

| C# Property | JSON Property |
|-------------|---------------|
| `BusinessName` | `business_name` |
| `FirstName` | `first_name` |
| `EmailVerified` | `email_verified` |
| `CreatedAt` | `created_at` |
| `IsActive` | `is_active` |
| `ValueProposition` | `value_proposition` |
| `CoreValues` | `core_values` |
| `CoreValuesStatus` | `core_values_status` |

## Frontend Implementation

### TypeScript/JavaScript

Create a utility function to convert objects to snake_case:

```typescript
/**
 * Converts object keys from camelCase to snake_case recursively
 */
export function toSnakeCase(obj: any): any {
  if (obj === null || obj === undefined || typeof obj !== 'object') {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.map(toSnakeCase);
  }

  return Object.keys(obj).reduce((result, key) => {
    const snakeKey = key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
    result[snakeKey] = toSnakeCase(obj[key]);
    return result;
  }, {} as any);
}

/**
 * Converts object keys from snake_case to camelCase recursively
 */
export function toCamelCase(obj: any): any {
  if (obj === null || obj === undefined || typeof obj !== 'object') {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.map(toCamelCase);
  }

  return Object.keys(obj).reduce((result, key) => {
    const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
    result[camelKey] = toCamelCase(obj[key]);
    return result;
  }, {} as any);
}
```

### Usage in API Calls

```typescript
// Before sending request
const requestData = {
  businessName: "Purpose Path",
  website: "https://purposepath.ai",
  step3: {
    niche: "Small Businesses",
    ica: "Business owner",
    valueProposition: "Transform values into action"
  }
};

// Convert to snake_case before sending
const apiPayload = toSnakeCase(requestData);
// Result: { business_name: ..., step3: { value_proposition: ... } }

await fetch('/business/onboarding', {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(apiPayload)
});

// Convert response from snake_case to camelCase
const response = await fetch('/business/onboarding');
const data = await response.json();
const camelData = toCamelCase(data.data);
// Now you can use: camelData.businessName, camelData.step3.valueProposition, etc.
```

## Why snake_case?

1. **Consistency with Python Services**: The hybrid architecture includes Python services that use snake_case by convention
2. **Database Consistency**: DynamoDB attribute names use snake_case
3. **URL Consistency**: API routes use kebab-case (`/business/onboarding`), which aligns better with snake_case than camelCase
4. **Team Standard**: Established convention across the codebase

## Common Mistakes

### ❌ Mixing naming conventions

```json
{
  "businessName": "Purpose Path",  // camelCase
  "website": "https://purposepath.ai",
  "step4": {
    "coreValues": ["Empathy"],     // camelCase
    "core_values_status": null     // snake_case
  }
}
```

**Problem**: Backend will deserialize `core_values_status` correctly but ignore `coreValues` because it expects `core_values`.

### ❌ Partial conversion

Some fields converted, some not. This commonly happens when:
- Using different serialization libraries for different parts of the frontend
- Manual object construction without using the utility function
- Copy-pasting examples from different sources

## Validation

### Manual Testing

Use the actual JSON property names in curl/Postman:

```bash
# ✅ Correct
curl -X PUT https://api.dev.purposepath.app/account/api/v1/business/onboarding \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"business_name":"Test","core_values":["Value1"]}'

# ❌ Wrong
curl -X PUT https://api.dev.purposepath.app/account/api/v1/business/onboarding \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"businessName":"Test","coreValues":["Value1"]}'
```

### Automated Testing

Add tests to verify JSON serialization:

```typescript
describe('API Serialization', () => {
  it('converts request to snake_case', () => {
    const input = { businessName: 'Test', coreValues: ['A'] };
    const output = toSnakeCase(input);
    expect(output).toEqual({ business_name: 'Test', core_values: ['A'] });
  });

  it('converts response to camelCase', () => {
    const input = { business_name: 'Test', core_values: ['A'] };
    const output = toCamelCase(input);
    expect(output).toEqual({ businessName: 'Test', coreValues: ['A'] });
  });
});
```

## Reference

- **C# Implementation**: `PurposePath.Shared/Common/JsonSnakeCaseNamingPolicy.cs`
- **Configuration**: `PurposePath.Shared/Lambda/BaseLambdaFunction.cs` (line 172)
- **API Specifications**: `docs/shared/Specifications/`
- **Related Issue**: #160 - Frontend snake_case conversion for PUT /business/onboarding

## Questions?

If you're unsure about a property name:
1. Check the API specification docs in `docs/shared/Specifications/`
2. Look at the C# DTO class and convert `PascalCase` → `snake_case`
3. Test with a curl command before integrating into frontend code
4. Check CloudWatch logs - deserialization errors will show which properties failed to bind
