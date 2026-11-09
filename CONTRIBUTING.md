# Contributing to TakeHome

Thanks for your interest! TakeHome is an open-source project built for the PayPal AI Hackathon.

## Run it locally
1. Clone the repo and create a virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your keys (never commit `.env`).
4. Start the app: `uvicorn backend.app.main:app --reload`

## Run the tests
`pytest`

## Making changes
- Open an issue before starting a large change.
- Keep pull requests small and focused.
- Never commit API keys or secrets. Use environment variables.
- PayPal features use the **sandbox** only.

## Reporting security issues
Please open a private report or contact the maintainer instead of posting details publicly.
