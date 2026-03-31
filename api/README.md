# FinFresh Backend API

## Architecture Decisions
- **FastAPI:** Chosen for its high performance, automatic Swagger documentation, and native asynchronous support.
- **MongoDB:** Used for its flexibility in handling financial transaction data which might vary in categories.

## Financial Health Score Algorithm
The score is calculated out of 100 based on 4 key components (25 pts each):
1. **Emergency Fund:** Measures months of coverage (Total Savings / Avg Expenses).
2. **Savings Rate:** (Monthly Savings / Monthly Income) * 100.
3. **Debt Ratio:** (Monthly Debt Payments / Monthly Income) * 100.
4. **Investment Ratio:** (Monthly Investments / Monthly Income) * 100.

## MongoDB Schema
- **Users:** `_id, name, email, passwordHash, createdAt`
- **Transactions:** `_id, userId, type (enum), category, amount, date, description`