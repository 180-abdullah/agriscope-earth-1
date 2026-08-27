.PHONY: install run api test docker

install:
	python -m pip install -r requirements.txt -r backend/requirements-dev.txt

run:
	streamlit run streamlit_app.py

api:
	uvicorn backend.app.main:app --reload --port 8000

test:
	python -m pytest backend/tests tests/test_streamlit_app.py -q

docker:
	docker compose -f docker-compose.streamlit.yml up --build
