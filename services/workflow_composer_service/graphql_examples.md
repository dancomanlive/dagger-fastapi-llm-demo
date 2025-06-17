# Sample GraphQL Queries for Workflow Composer Service

## 1. Get all services and their activities
```graphql
{
  services {
    name
    activities {
      id
      name
      description
      parameters {
        name
        type
        description
        required
      }
      returns {
        type
        description
      }
    }
  }
}
```

## 2. Get details for a specific activity
```graphql
{
  activity(id: "utility_service.validate_inputs_activity") {
    id
    service
    name
    description
    taskQueue
    timeoutSeconds
    retryAttempts
    parameters {
      name
      type
      description
      required
    }
    returns {
      type
      description
    }
  }
}
```

## 3. List all workflows
```graphql
{
  workflows {
    name
    description
    version
    activities
  }
}
```

## 4. Create a new workflow (Mutation)
```graphql
mutation CreateWorkflow {
  createWorkflow(
    name: "GraphQLComposedWorkflow"
    description: "A workflow created using GraphQL"
    activities: """[
      {
        "id": "utility_service.validate_inputs_activity",
        "result_key": "validated_inputs",
        "parameters": [
          {
            "name": "inputs",
            "source": "input",
            "input_name": "user_data"
          }
        ]
      },
      {
        "id": "utility_service.format_response_activity",
        "result_key": "formatted_output",
        "parameters": [
          {
            "name": "results",
            "source": "activity_result",
            "result_name": "validated_inputs"
          },
          {
            "name": "format_type",
            "source": "input",
            "input_name": "format"
          }
        ]
      }
    ]"""
  )
}
```

## 5. Execute a workflow (Mutation)
```graphql
mutation ExecuteWorkflow {
  executeWorkflow(
    name: "GraphQLComposedWorkflow"
    inputs: """{"user_data": {"message": "Hello GraphQL"}, "format": "json"}"""
  )
}
```

## 6. Execute a single activity for testing (Mutation)
```graphql
mutation TestActivity {
  executeActivity(
    activityId: "utility_service.validate_inputs_activity"
    inputs: """{"inputs": {"test": "data"}}"""
  )
}
```

## 7. Complex query with nested data
```graphql
{
  services {
    name
    activities {
      name
      description
      parameters {
        name
        type
        required
      }
    }
  }
  workflows {
    name
    description
    version
  }
}
```

## How to use these queries:

1. Open the GraphiQL playground at: http://localhost:8001/graphql
2. Copy any of the above queries into the left panel
3. Click the "Play" button to execute
4. View results in the right panel
5. Use the schema explorer (Docs tab) to discover available fields

## Schema Introspection Query:
```graphql
{
  __schema {
    types {
      name
      description
      fields {
        name
        type {
          name
        }
      }
    }
  }
}
```
