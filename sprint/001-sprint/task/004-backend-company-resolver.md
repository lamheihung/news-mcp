# Task 004: Backend - Company Resolver

## Description
Implement the `resolve_company` function that normalizes any company identifier to a Bloomberg ticker by calling the Gemini API.

## Requirements
- Implement `resolve_company(identifier: str) -> Company` in `src/resolver.py`.
- Use the `google-genai` client to ask Gemini for the Bloomberg ticker, company name, and aliases.
- Parse the API response into a validated `Company` model.
- Require the `GEMINI_API_KEY` environment variable and fail clearly when it is missing.
- Surface API or parsing errors with informative exception messages.

## Dependencies
- Blocks: [005, 007, 008]
- Blocked by: [001, 003]
- Parallelizable with: [002]

## Success Criteria (5 points)
1. `resolve_company("Apple")` returns a `Company` with a non-empty `bloomberg_ticker`.
2. `resolve_company` raises a clear error when `GEMINI_API_KEY` is not set.
3. The implementation uses the `google-genai` client and a structured prompt.
4. API errors or unparseable responses raise an exception with a readable message.
5. The returned `Company` includes at least one alias in addition to the input identifier.

## Status
[004-backend-company-resolver-status.md](../status/004-backend-company-resolver-status.md)
