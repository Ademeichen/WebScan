
## 7. CI/CD Pipeline

The project uses GitHub Actions for Continuous Integration. The pipeline is defined in `.github/workflows/ci.yml`.

### 7.1 Workflow Triggers
*   **Push**: Triggers on push to `main` or `master` branches.
*   **Pull Request**: Triggers on PRs targeting `main` or `master`.

### 7.2 Pipeline Steps
1.  **Environment Setup**: Sets up Python environment (testing against 3.9, 3.10, 3.11).
2.  **Dependency Installation**: Installs requirements from `requirements.txt` and testing tools (`pytest`, `pytest-asyncio`).
3.  **Testing**: Runs the integration test suite (`backend/tests/test_integration_new.py`) to verify the core logic of the Dynamic POC Verification Engine and its integration with the Task Executor.

### 7.3 Future Enhancements
*   **Linting**: Add `flake8` or `black` for code style enforcement.
*   **Docker Build**: Automatically build and push Docker images on successful tests.
*   **Deployment**: Auto-deploy to staging environment on merge to main.
