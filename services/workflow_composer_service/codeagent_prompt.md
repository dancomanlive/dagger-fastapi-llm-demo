"""
CODEAGENT PROMPT: Enhanced Dynamic services.yaml Generation with Intelligent Error Analysis

TASK OBJECTIVE:
Generate a complete and valid services.yaml configuration for the SmartÆgent X-7 platform using ONLY GraphQL API introspection. Use an intelligent ReAct (Reasoning + Acting) loop with enhanced error analysis to distinguish between different types of failures.

STRICT CONSTRAINTS:
1. Use ONLY the GraphQL API at http://localhost:8001/graphql for service/activity discovery
2. DO NOT access any files directly - use only API introspection
3. Generate services.yaml that passes ALL validation tests
4. Use intelligent error analysis to distinguish between content errors vs environment errors
5. Retry up to 5 times, but only if the error type suggests it would be beneficial

REQUIRED TOOLS TO USE:
1. discover_services_complete() - for complete service discovery (optimized single-call GraphQL query)
2. generate_services_yaml_from_graphql() - for YAML generation based on discovered services
3. validate_services_yaml_with_tests() - for validation with structured error analysis
4. save_generated_services_yaml() - for saving the final validated configuration

Note: The discover_services_complete() tool is all you need for discovery - it contains a pre-optimized GraphQL query that gets all service details, activities, parameters, return types, timeouts, and system status in one efficient call.

ENHANCED ERROR ANALYSIS:
When validate_services_yaml_with_tests() fails, analyze the error_type field:
- "environment_error": Test script missing, environment issue - DO NOT retry YAML generation
- "yaml_content_error": Actual YAML validation failures - analyze failed tests and regenerate improved YAML
- "file_not_found": Generated YAML file missing - ensure save step completed successfully

INTELLIGENT WORKFLOW:
1. Use discover_services_complete() to get ALL service information in one efficient call
2. Generate services.yaml structure with generate_services_yaml_from_graphql()
3. Save the YAML with save_generated_services_yaml()
4. Run validation with validate_services_yaml_with_tests()
5. IF validation fails:
   a. Check error_type in the response
   b. If "environment_error": Report environment issue, do not retry
   c. If "yaml_content_error": Analyze failed_tests details and regenerate improved YAML
   d. If "file_not_found": Verify save step and retry
6. Repeat steps 4-5 until success or max 5 iterations for content errors only

SUCCESS CRITERIA:
- All services.yaml validation tests must pass
- Configuration must include all discovered services and activities
- Agent must demonstrate intelligent error analysis, not blind retries
- Must distinguish between fixable content errors and unfixable environment errors

TARGET OUTPUT:
A complete services.yaml file saved to generated/services_dynamic.yaml that passes all validation tests and contains all services/activities discovered via GraphQL API introspection.

Begin the enhanced ReAct loop now. Use reasoning to plan your approach, then act by calling the appropriate tools. Pay special attention to error analysis and avoid inefficient retry loops.
"""
