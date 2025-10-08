# Pull Request

## Summary

Briefly describe the change and why it’s needed.

## Checklist

- [ ] I reviewed `ENGINEERING_GUIDE.md`
- [ ] API changes match `docs/frontend-integration-guide.md` (or I updated it)
- [ ] Responses use `ApiResponse[...]` with snake_case keys
- [ ] Tests added/updated and pass locally (`pytest -q`)
- [ ] Updated/Created `docs/frontend-alignment-plan.md` if scope affects alignment

## Testing

How did you test this change? Include commands, test cases, and results.

```pwsh
$env:PYTHONPATH="c:\\Projects\\XBS\\PurposePath\\PurposePath_Api;account;coaching;traction"; pytest -q
```

## Screenshots/Logs (optional)
