install:
	@echo "Installing..."
	@cd ui && npm install
	@cd python-backend && pip install -r requirements.txt

run-backend:
	@echo "Running Python Backend..."
	@cd python-backend && python app.py

run-ui:
	@echo "Running UI..."
	@cd ui && npm run dev