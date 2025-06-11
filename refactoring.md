Okay, here is a detailed step-by-step plan for the TDD refactoring, designed to be executed incrementally.

**Phase 1: Refactor `embedding_service` to use a Temporal Activity**

**Goal:** Replace the HTTP endpoint-based embedding logic (called by `temporal_service`) with a Temporal activity within `embedding_service`.

*   **Step 1.1: Define the Embedding Activity Interface (Test-First)**
    *   **RED (Test for Activity Signature & Basic Logic - `embedding_service`)**
        *   Create a new test file, e.g., `services/embedding_service/tests/test_activities.py`.
        *   Write a test function (e.g., `test_perform_embedding_and_indexing_activity_structure`).
        *   This test will try to import `perform_embedding_and_indexing_activity` from `services/embedding_service/activities.py` (which doesn't exist yet, so it will fail).
        *   The test should define sample input documents and a collection name.
        *   It should assert that if the activity were called (even with a placeholder implementation), it would be callable with these arguments.
        *   *Initial failure: Import error or NameError.*
    *   **GREEN (Create Activity Stub - `embedding_service`)**
        *   Create `services/embedding_service/activities.py`.
        *   Define a stub for `perform_embedding_and_indexing_activity` with the correct signature (accepting documents and collection name) and a placeholder implementation (e.g., `pass` or `return {}`).
        *   *Test should now pass the import and basic call structure.*
    *   **REFACTOR (N/A for stub)**

*   **Step 1.2: Test Core Logic of Embedding Activity (Unit Test)**
    *   **RED (Test Activity Logic - `embedding_service`)**
        *   In `services/embedding_service/tests/test_activities.py`, write a new test (e.g., `test_perform_embedding_and_indexing_activity_logic`).
        *   Mock the `QdrantClient` and its methods (`get_collection`, `create_collection`, `upsert_points`, `get_embedding_size`, `close`).
        *   Provide sample documents.
        *   Call `perform_embedding_and_indexing_activity` with the sample documents and a collection name.
        *   Assert that the mocked Qdrant client methods are called with the expected arguments (e.g., correct collection name, correctly transformed points from documents).
        *   Assert the activity returns the expected success structure (e.g., `{"status": "success", "indexed_count": len(documents), ...}`).
        *   *Initial failure: Assertions for Qdrant calls and return value will fail.*
    *   **GREEN (Implement Activity Logic - `embedding_service`)**
        *   Implement the full logic inside `perform_embedding_and_indexing_activity` in `services/embedding_service/activities.py`. This will involve:
            *   Initializing `QdrantClient` (using environment variables for host, etc., as in your example).
            *   Logic to check/create collection.
            *   Transforming input documents into `PointStruct` objects.
            *   Calling `qdrant_client.upsert_points`.
            *   Returning the success message.
        *   *Make the test pass.*
    *   **REFACTOR (Clean up Activity Code - `embedding_service`)**
        *   Review the activity implementation for clarity, error handling (e.g., `try...finally` for client closure), and adherence to best practices.

*   **Step 1.3: Test Embedding Worker Registration**
    *   **RED (Test Worker Registers Activity - `embedding_service`)**
        *   Create/modify a test file for worker setup, e.g., `services/embedding_service/tests/test_worker.py`.
        *   Write a test (e.g., `test_embedding_worker_registers_activity`).
        *   This test will need to mock `temporalio.Client.connect`, `client.new_worker`, and `worker.run`.
        *   The core idea is to assert that when the worker setup code is run, `client.new_worker` is called with the correct task queue name (e.g., `"embedding-task-queue"`) and that the `activities` argument includes `perform_embedding_and_indexing_activity`.
        *   *Initial failure: No worker setup code exists, or it doesn't register the activity correctly.*
    *   **GREEN (Implement Worker Setup - `embedding_service`)**
        *   In main.py (or a new `worker.py`), add the Temporal worker setup:
            *   Import `Client`, `Worker`, and `perform_embedding_and_indexing_activity`.
            *   Define the task queue name (e.g., `EMBEDDING_TASK_QUEUE = "embedding-task-queue"`).
            *   Write an async function `run_worker()` that connects the client, creates a worker with the activity and task queue, and runs the worker.
            *   Call this `run_worker()` in the `if __name__ == "__main__":` block.
        *   *Make the test pass.*
    *   **REFACTOR (Clean up Worker Code - `embedding_service`)**
        *   Ensure configuration (Temporal address, namespace, task queue) is handled cleanly (e.g., via environment variables).

**Phase 2: Refactor `temporal_service` to Use the New Embedding Activity**

**Goal:** Modify `DocumentProcessingWorkflow` to call the new `perform_embedding_and_indexing_activity` via Temporal instead of its local HTTP-calling activity.

*   **Step 2.1: Test Workflow Calls New Embedding Activity**
    *   **RED (Test Workflow Activity Call - `temporal_service`)**
        *   In `services/temporal_service/tests/test_workflows.py`, modify the existing tests for `DocumentProcessingWorkflow` (or create a focused one like `test_document_processing_workflow_calls_embedding_activity`).
        *   Use `temporalio.testing.WorkflowEnvironment` or mock `workflow.execute_activity`.
        *   When testing the workflow's `run` method:
            *   Assert that `workflow.execute_activity` is called with:
                *   Activity name: `"perform_embedding_and_indexing"` (the string name).
                *   Arguments: The chunked documents and the target collection name.
                *   Task queue: `EMBEDDING_SERVICE_TASK_QUEUE` (e.g., `"embedding-task-queue"`).
                *   Appropriate timeouts and retry policies.
            *   Provide a mock return value for this `execute_activity` call.
            *   Assert the rest of the workflow logic proceeds correctly based on this mocked return.
        *   The local `embed_documents_activity` (that makes HTTP calls) should no longer be called for this step.
        *   *Initial failure: Workflow still calls the old activity or calls the new one incorrectly.*
    *   **GREEN (Modify Workflow - `temporal_service`)**
        *   In workflows.py:
            *   Remove or comment out the call to the old local `embed_documents_activity`.
            *   Add the `await workflow.execute_activity(...)` call targeting `"perform_embedding_and_indexing"` on the `EMBEDDING_SERVICE_TASK_QUEUE`.
            *   Ensure arguments (chunked docs, collection name) are passed correctly.
            *   Define `EMBEDDING_SERVICE_TASK_QUEUE` as a constant or get from config.
        *   *Make the test pass.*
    *   **REFACTOR (Clean up Workflow - `temporal_service`)**
        *   Review the workflow for clarity. The old `embed_documents_activity` in activities.py can now be marked as deprecated or removed if no longer needed by any workflow.

*   **Step 2.2: Integration Test (Workflow to Activity - Optional but Recommended)**
    *   **RED (Test Full Workflow-Activity Flow)**
        *   Using `temporalio.testing.WorkflowEnvironment`, write a test that executes the `DocumentProcessingWorkflow`.
        *   The environment should be configured to run a worker for the `EMBEDDING_SERVICE_TASK_QUEUE` that can execute the *actual* `perform_embedding_and_indexing_activity` (from `embedding_service`).
        *   You'll still need to mock the Qdrant client within the activity for this test to keep it isolated from a live Qdrant instance.
        *   Start the workflow and assert its successful completion and expected final result.
        *   *Initial failure: Issues in wiring, task queue names, activity arguments, or activity logic.*
    *   **GREEN (Fix Integration Issues)**
        *   Debug and fix any issues in the workflow definition, activity registration, activity implementation, or test setup until the workflow runs end-to-end successfully within the test environment.
    *   **REFACTOR (Test Setup)**

**Phase 3: Refactor `retriever_service` to use a Temporal Activity**

**Goal:** Expose search/retrieval logic as a Temporal activity.

*   **Step 3.1: Define & Test `SearchDocumentsActivity` (Unit Test - `retriever_service`)**
    *   Follow the same pattern as Step 1.1 and 1.2 for `embedding_service`:
        *   **RED**: Test for activity signature and logic in `services/retriever_service/tests/test_activities.py` for `search_documents_activity`. Mock `QdrantClient` and its query methods. Assert correct Qdrant calls and result transformation.
        *   **GREEN**: Implement `search_documents_activity` in `services/retriever_service/activities.py` (or similar) with Qdrant client interaction.
        *   **REFACTOR**: Clean up.

*   **Step 3.2: Test Retriever Worker Registration (`retriever_service`)**
    *   Follow the same pattern as Step 1.3:
        *   **RED**: Test in `services/retriever_service/tests/test_worker.py` that a worker registers `search_documents_activity` on a specific task queue (e.g., `"retrieval-task-queue"`).
        *   **GREEN**: Implement worker setup in main.py (or `worker.py`).
        *   **REFACTOR**: Clean up.

**Phase 4: Integrate Retrieval Activity into a Workflow**

**Goal:** Create or modify a workflow (likely in `temporal_service` or a new dedicated workflow) to use `SearchDocumentsActivity`.

*   **Step 4.1: Test Workflow Calls `SearchDocumentsActivity`**
    *   Follow the same pattern as Step 2.1:
        *   **RED**: In `services/temporal_service/tests/test_workflows.py` (or a new test file if it's a new workflow), test that a workflow (e.g., a new `RetrievalWorkflow` or an existing one) calls `workflow.execute_activity` for `"search_documents"` on the `"retrieval-task-queue"` with correct arguments (query, top_k). Mock its return.
        *   **GREEN**: Implement/modify the workflow in workflows.py (or new workflow file) to call the activity.
        *   **REFACTOR**: Clean up.

*   **Step 4.2: Integration Test (Workflow to Search Activity - Optional)**
    *   Follow the same pattern as Step 2.2, using `WorkflowEnvironment` to test the workflow calling the actual `search_documents_activity` (with Qdrant mocked).

**Phase 5: Refactor `gradio_service` to Interact via Temporal Client**

**Goal:** `gradio_service` should initiate workflows instead of making direct HTTP calls to other services for core processing.

*   **Step 5.1: Test Gradio Initiates Document Processing Workflow**
    *   **RED (Test Workflow Start - `gradio_service`)**
        *   In a test file for `gradio_service`'s backend logic (e.g., `services/gradio_service/tests/test_handlers.py`).
        *   Identify the Gradio event handler that currently triggers document processing (likely via an HTTP call to `temporal_service`'s `/process_documents` endpoint).
        *   Write a test for this handler.
        *   Mock `temporalio.Client.connect` and the `client.start_workflow` method.
        *   Simulate the Gradio event.
        *   Assert that `client.start_workflow` is called with:
            *   Workflow name: `DocumentProcessingWorkflow` (or its string name).
            *   Arguments: The documents from Gradio.
            *   Task queue: The one `temporal_service` worker listens on for this workflow.
            *   Correct workflow ID, etc.
        *   *Initial failure: Handler still makes HTTP call or doesn't call `start_workflow`.*
    *   **GREEN (Modify Handler - `gradio_service`)**
        *   In `services/gradio_service/...` (where the handler logic is):
            *   Import `temporalio.Client`.
            *   In the handler, initialize a Temporal client (can be done once globally or per request, consider lifecycle).
            *   Replace the HTTP call with `await client.start_workflow(...)`.
            *   Handle the `WorkflowHandle` returned (e.g., to get results later or just confirm start).
        *   *Make the test pass.*
    *   **REFACTOR (Client Management, Error Handling - `gradio_service`)**
        *   Ensure Temporal client is managed efficiently. Add error handling for workflow start failures.

*   **Step 5.2: Test Gradio Initiates Retrieval (if applicable)**
    *   If Gradio has a search feature that currently calls `retriever_service` via HTTP:
        *   **RED**: Similar to 5.1, test that the Gradio search handler calls `client.start_workflow` (for `RetrievalWorkflow` or signals an existing workflow) or `client.execute_workflow` if it's a short-lived query. Assert correct parameters.
        *   **GREEN**: Modify the Gradio search handler to use the Temporal client.
        *   **REFACTOR**.

**General Considerations During TDD:**

*   **Configuration**: Ensure Temporal server addresses, namespaces, and task queue names are configurable (e.g., via environment variables) and accessible to both tests and application code.
*   **Mocking**: Be precise about what you're mocking. For activity unit tests, mock external I/O (Qdrant). For workflow unit tests, mock `workflow.execute_activity`. For `WorkflowEnvironment` tests, mock I/O *within* the activities if you don't want to hit live external systems.
*   **Small Steps**: Keep each Red-Green-Refactor cycle small and focused.
*   **Run All Tests Frequently**: After each Green and Refactor step, run all tests in the suite to catch regressions.

This detailed plan should guide the step-by-step TDD refactoring process. Each step builds upon the previous ones, gradually transforming your architecture.