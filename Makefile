dev:
	poetry run uvicorn backend.main:app --reload

test:
	poetry run pytest -q
