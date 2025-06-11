Feature: Gradio service Temporal integration
  As a user of the RAG system
  I want the Gradio interface to use Temporal workflows for document retrieval
  So that all services are properly orchestrated through Temporal

  Background:
    Given the Temporal server is running
    And the RetrievalWorkflow is registered
    And the gradio service is configured to use Temporal

  Scenario: User queries through Gradio interface using Temporal
    Given a user opens the Gradio chat interface
    When the user submits a query "What is artificial intelligence?"
    And selects collection "document_chunks"
    Then the gradio service should start a RetrievalWorkflow
    And the workflow should retrieve relevant document contexts
    And the OpenAI response should include context from the workflow
    And no HTTP calls should be made to retriever service

  Scenario: Gradio handles Temporal workflow failures gracefully
    Given the Temporal workflow fails during retrieval
    When a user submits a query through Gradio
    Then the gradio service should return an error message
    And the chat interface should remain functional
    And the user should be notified of the retrieval error

  Scenario: Multiple users can query simultaneously through Temporal
    Given multiple users are using the Gradio interface
    When each user submits different queries
    Then each query should start its own RetrievalWorkflow
    And all workflows should execute independently
    And each user should receive their own contextual response

  Scenario: Gradio workflow integration with different collections
    Given documents are stored in multiple collections
    When a user selects collection "default" and queries "machine learning"
    Then the RetrievalWorkflow should search in the "default" collection
    When a user selects collection "document_chunks" and queries "AI ethics"
    Then the RetrievalWorkflow should search in the "document_chunks" collection

  Scenario: Complete RAG pipeline with OpenAI integration
    Given the Temporal server is running
    And the RetrievalWorkflow is registered
    And the OpenAI API is available
    When a user submits a query "What is artificial intelligence?" through Gradio
    And the Temporal workflow provides relevant context
    Then OpenAI should receive the workflow context in the system prompt
    And generate a response using that context
    And the user should see the contextual AI response
    And the debug panel should show the retrieved documents
