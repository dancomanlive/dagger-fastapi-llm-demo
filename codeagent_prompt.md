"""
CODEAGENT PROMPT: Dynamic services.yaml Generation with Test-Driven ReAct Loop

TASK OBJECTIVE:
Generate a complete and valid services.yaml configuration for the SmartÆgent X-7 platform using ONLY GraphQL API introspection. Use a ReAct (Reasoning + Acting) loop with test-driven validation to iterate until all tests pass.

STRICT CONSTRAINTS:
1. Use ONLY the GraphQL API at http://localhost:8001/graphql for service/activity discovery
2. DO NOT access any files directly - use only API introspection
3. Generate services.yaml that passes ALL validation tests
4. Use test failures to guide improvements (ReAct methodology)
5. Retry up to 5 times until all tests pass

REQUIRED TOOLS TO USE:
1. discover_services() - for initial service discovery
2. query_graphql() - for custom GraphQL queries
3. generate_services_yaml_from_graphql() - for GraphQL-based introspection
4. validate_services_yaml_with_tests() - for running validation tests 
5. save_generated_services_yaml() - for saving final validated config

Note: The agent should use its own reasoning to analyze test failures and improve the configuration iteratively, rather than relying on a separate improvement tool.

EXPECTED WORKFLOW:
1. Use discover_services() to get initial service list
2. Use query_graphql() for detailed service/activity introspection
3. Generate initial services.yaml structure with generate_services_yaml_from_graphql()
4. Run comprehensive validation tests with validate_services_yaml_with_tests()
5. If tests fail: reason about failures and regenerate improved configuration
6. Repeat steps 4-5 until all tests pass (max 5 iterations)
7. Save the final validated services.yaml with save_generated_services_yaml()

SUCCESS CRITERIA:
- All services.yaml validation tests must pass
- Configuration must include all discovered services and activities
- Generated config should match or exceed the original services.yaml in completeness
- Agent must demonstrate ReAct loop: reasoning about test failures and taking corrective actions

TARGET OUTPUT:
A complete services.yaml file saved to generated/services_dynamic.yaml that passes all validation tests and contains all services/activities discovered via GraphQL API introspection.

VALIDATION REQUIREMENTS:
The generated services.yaml must pass these test categories:
- Structure validation (required keys, correct nesting)
- Content validation (non-empty services, activities, pipelines)
- Schema compliance (correct data types, required fields)
- Completeness validation (all expected services and activities present)
- Logical consistency (valid pipeline definitions, activity references)

Begin the ReAct loop now. Use reasoning to plan your approach, then act by calling the appropriate tools.
"""
