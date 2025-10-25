## InvestoMommy

This repository contains the backend for InvestoMommy.

## Setup

You will need the following values in your .env value
```
FMP_API_KEY="Get API key from the FMP site"
BALANCE_SHEET_API_URL="https://financialmodelingprep.com/stable/balance-sheet-statement?symbol={}&apikey={}"
INCOME_STATEMENT_API_URL="https://financialmodelingprep.com/stable/income-statement?symbol={}&apikey={}"
KEY_METRICS_API_URL="https://financialmodelingprep.com/stable/key-metrics?symbol={}&apikey={}"
EMPLOYEE_COUNT_API_URL="https://financialmodelingprep.com/stable/employee-count?symbol={}&apikey={}"
SUPABASE_URL="Get Supabase URL from owner"
SUPABASE_KEY="Get Suapbase key from owner"
```

Follow these steps to create a Python virtual environment and install the project's dependencies.

1) Create a virtual environment

	On Windows (recommended command):

	```
	py -m venv .venv
	```

	If `py` is not available (common on macOS/Linux), use:

	```
	python3 -m venv .venv
	```

2) Activate the virtual environment

	- macOS / Linux (zsh, bash):

	  ```
	  source .venv/bin/activate
	  ```

	- Windows (Command Prompt):

	  ```
	  .venv\Scripts\activate
	  ```

	- Windows (PowerShell):

	  ```
	  .venv\Scripts\Activate.ps1
	  ```

3) (Optional) Upgrade pip inside the venv

	```
	python -m pip install --upgrade pip
	```

4) Install requirements

	```
	pip install -r requirements.txt
	```

5) Run the server using
	```
	fastapi dev server.py
	```