@integration
Feature: Document Processing Workflow Integration
  As a system operator
  I want to process documents through the complete workflow pipeline
  So that documents are properly chunked, embedded, and indexed via Temporal activities

  Background:
    Given the temporal environment is set up
    And the embedding service worker is available
    And the temporal service worker is available

  @workflow @embedding
  Scenario: Process documents through complete workflow pipeline
    Given I have a list of documents to process:
      | id   | text                              | source    |
      | doc1 | This is the first test document.  | test.txt  |
      | doc2 | This is the second test document. | test2.txt |
    When I start the document processing workflow
    Then the workflow should complete successfully
    And the documents should be chunked into paragraphs
    And the chunks should be embedded and indexed
    And the workflow result should contain processing statistics

  @health
  Scenario: Health check workflow works correctly
    Given the temporal environment is ready
    When I execute the health check workflow
    Then the health check should return successfully
    And indicate the system is healthy

  @workflow @retrieval
  Scenario: Retrieve documents through RetrievalWorkflow
    Given the retrieval service worker is available
    When I start the retrieval workflow with query "test search"
    Then the workflow should complete successfully
    And the search activity should be called with correct parameters
    And the workflow result should contain search results

  @activity @chunking
  Scenario: Chunking activity processes documents correctly
    Given I have documents ready for chunking:
      | id   | text                              |
      | doc1 | This is the first test document.  |
      | doc2 | This is the second test document. |
    When I execute the chunking activity directly
    Then the documents should be chunked successfully
    And the chunks should have proper metadata
    And the activity should return chunk information
