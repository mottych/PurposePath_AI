# API Naming Conventions

## JSON Property Naming Standard

**Default standard: API request/response JSON uses `camelCase`.**

This aligns with the `docs/shared/Specifications/api-fe/` contracts and current frontend service implementations.
Use snake_case only when a specification explicitly marks a legacy/backward-compatible path.

## Examples

### ✅ CORRECT - camelCase (default)

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

### ❌ INCORRECT - snake_case (unless endpoint explicitly says so)

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

## C# to JSON Mapping

For APIs that follow default ASP.NET Core JSON settings, C# `PascalCase` maps to `camelCase` JSON:

| C# Property | JSON Property |
| ------------- | --------------- |
| `BusinessName` | `businessName` |
| `FirstName` | `firstName` |
| `EmailVerified` | `emailVerified` |
| `CreatedAt` | `createdAt` |
| `IsActive` | `isActive` |
| `ValueProposition` | `valueProposition` |
| `CoreValues` | `coreValues` |
| `CoreValuesStatus` | `coreValuesStatus` |

## Frontend Implementation

### TypeScript/JavaScript

Use camelCase in frontend domain models and API client payloads by default.
Do not apply blanket object-key conversion unless a specific endpoint contract requires it.

```typescript
export type BusinessPayload = {
  businessName: string;
  website: string;
  step3: {
    niche: string;
    ica: string;
    valueProposition: string;
  };
};
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

await fetch('/business/onboarding', {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(requestData)
});
```

## Exceptions and Legacy Compatibility

Some endpoints still accept snake_case for backward compatibility. Use only when explicitly documented.

- `account-api.md`: logout refresh token supports legacy `refresh_token` while canonical query field is `refreshToken`.
- `traction-service/insights-api.md`: Python AI payload ingestion may include snake_case input fields; API responses remain camelCase.

## Common Mistakes

### ❌ Mixing naming conventions without endpoint-specific contract

```json
{
  "businessName": "Purpose Path",  // camelCase
  "website": "https://purposepath.ai",
  "step4": {
    "coreValues": ["Empathy"],
    "core_values_status": null
  }
}
```

**Problem**: Mixed conventions create contract ambiguity and mapping bugs. Follow the exact casing documented per endpoint.

### ❌ Assumptions based on old docs

Most current `api-fe` specs are camelCase-first. Do not assume snake_case unless the endpoint spec calls it out as legacy/compatibility behavior.

## Validation

### Manual Testing

Use the exact property casing from the endpoint specification:

```bash
# ✅ Correct (camelCase default)
curl -X PUT https://api.dev.purposepath.app/account/api/v1/business/onboarding \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"businessName":"Test","coreValues":["Value1"]}'

# ❌ Wrong for camelCase endpoints
curl -X PUT https://api.dev.purposepath.app/account/api/v1/business/onboarding \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"business_name":"Test","core_values":["Value1"]}'
```

### Automated Testing

Add tests that assert request/response casing for each endpoint contract:

```typescript
describe('API Contract Casing', () => {
  it('sends business onboarding in camelCase', () => {
    const payload = { businessName: 'Test', coreValues: ['A'] };
    expect(payload).toEqual({ businessName: 'Test', coreValues: ['A'] });
  });
});
```

## Reference

- **Master API FE Index**: `docs/shared/Specifications/api-fe/index.md`
- **Common Patterns**: `docs/shared/Specifications/api-fe/common-patterns.md`
- **Account API legacy note**: `docs/shared/Specifications/api-fe/account-api.md`
- **Insights API compatibility note**: `docs/shared/Specifications/api-fe/traction-service/insights-api.md`

## Questions?

If you're unsure about a property name:

1. Check the endpoint specification in `docs/shared/Specifications/api-fe/`.
2. Default to camelCase unless that endpoint explicitly documents a legacy snake_case input.
3. Validate with curl/Postman using the exact endpoint contract.
4. Add/adjust service-level tests to prevent casing drift.
