## InvestoMommy

This repository contains the backend for InvestoMommy.

## Setup

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