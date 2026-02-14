# Changelog

All notable changes to the AIAgent module will be documented in this file.

## [Unreleased] - 2026-02-02

### Added
- **Unified Task Model**: Replaced dual `Task`/`AgentTask` models with a single `Task` model for AI Agent scans, ensuring consistent state tracking across the system.
- **Serial Task Execution**: Implemented `TaskExecutor` with a serial queue to prevent concurrent resource conflicts during scans.
- **Idempotency Protection**: Added checks in `TaskExecutor` to prevent duplicate task submissions (using `queued_task_ids` and `running_task_id`).
- **Global Timeout Control**: Enforced a global timeout (default 1 hour) for all tasks executed via `TaskExecutor`.
- **Atomic Progress Events**: Added granular progress tracking for four key stages:
  - `openai`: Planning and analysis (TaskPlanningNode).
  - `plugins`: Tool execution (ToolExecutionNode).
  - `awvs`: AWVS vulnerability scanning (AWVSScanningNode).
  - `pocsuite3`: POC verification (POCVerificationNode).
- **WebSocket Integration**: Implemented real-time bidirectional communication for progress updates, replacing legacy polling mechanisms.
- **Unit Tests**: Added comprehensive unit tests for `AWVSScanningNode`, `ToolExecutionNode`, and `TaskExecutor` in `backend/tests/test_ai_agent.py`.

### Changed
- **API Endpoints**:
  - `POST /api/agent/scan`: Now creates a `Task` record and submits it to `task_executor` instead of triggering a background task directly.
  - `GET /api/agent/tasks/{task_id}`: Updated to prioritize `Task` model lookups while maintaining backward compatibility for legacy `AgentTask` records.
  - `GET /api/agent/tasks`: Updated to filter `Task` records by `task_type="ai_agent_scan"`.
- **AWVS Integration**: Refactored `AWVSScanningNode` to use `asyncio.to_thread` for non-blocking execution of synchronous AWVS API calls.
- **LangGraph Workflow**:
  - Integrated `AWVSScanningNode` and `POCVerificationNode` into the `ScanAgentGraph`.
  - Added retry limits to `_code_execution_result` to prevent infinite loops during capability enhancement.

### Fixed
- **Infinite Loop**: Resolved an issue where the agent could get stuck in a loop between code execution and capability enhancement by adding a retry counter.
- **Progress Display**: Fixed front-end progress bars by ensuring backend broadcasts atomic stage updates via WebSocket.
- **Task Scheduling**: Fixed the task queue logic to ensure strict serial execution of scanning tasks.
