#!/usr/bin/env python3
"""
Test script for the updated GraphQL schema with production discovery.
"""
import asyncio

# Import the schema directly
from gql_schema.schema import schema

async def test_graphql_queries():
    """Test various GraphQL queries with the new production discovery."""
    
    print("🧪 Testing GraphQL Schema with Production Discovery")
    print("=" * 60)
    
    # Test 1: Get all services
    print("\n1. Testing services query...")
    services_query = """
    query {
        services {
            name
            activityCount
            taskQueue
            workerIdentity
            health
            version
            temporalStatus
            activities {
                name
                description
                timeoutSeconds
                parameters {
                    name
                    type
                    description
                    required
                }
            }
        }
    }
    """
    
    try:
        result = await schema.execute(services_query)
        if result.errors:
            print(f"❌ Errors: {result.errors}")
        else:
            services = result.data['services']
            print(f"✅ Found {len(services)} services")
            for service in services:
                print(f"   - {service['name']}: {service['activityCount']} activities")
                print(f"     Task Queue: {service.get('taskQueue')}")
                print(f"     Worker Identity: {service.get('workerIdentity')}")
                print(f"     Health: {service.get('health')}")
                print(f"     Version: {service.get('version')}")
                print(f"     Temporal Status: {service.get('temporalStatus')}")
                for activity in service.get('activities', []):
                    print(f"       - {activity['name']}: {activity.get('description', 'No description')}")
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Get discovery info
    print("\n2. Testing discovery info query...")
    discovery_query = """
    query {
        discoveryInfo {
            discoveryMethod
            servicesDiscovered
            activitiesDiscovered
            temporalConnected
            metadataEndpointsAccessible
        }
    }
    """
    
    try:
        result = await schema.execute(discovery_query)
        if result.errors:
            print(f"❌ Errors: {result.errors}")
        else:
            info = result.data['discoveryInfo']
            print(f"✅ Discovery Method: {info['discoveryMethod']}")
            print(f"   Services: {info['servicesDiscovered']}")
            print(f"   Activities: {info['activitiesDiscovered']}")
            print(f"   Temporal Connected: {info['temporalConnected']}")
            print(f"   Metadata Endpoints: {info['metadataEndpointsAccessible']}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 3: Get Temporal status
    print("\n3. Testing Temporal status query...")
    temporal_query = """
    query {
        temporalStatus
    }
    """
    
    try:
        result = await schema.execute(temporal_query)
        if result.errors:
            print(f"❌ Errors: {result.errors}")
        else:
            queues = result.data['temporalStatus']
            print(f"✅ Active task queues: {queues}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 4: Generate services.yaml
    print("\n4. Testing services.yaml generation...")
    yaml_mutation = """
    mutation {
        generateServicesYaml {
            success
            servicesCount
            activitiesCount
            yamlContent
            errorMessage
        }
    }
    """
    
    try:
        result = await schema.execute(yaml_mutation)
        if result.errors:
            print(f"❌ Errors: {result.errors}")
        else:
            yaml_result = result.data['generateServicesYaml']
            print(f"✅ YAML Generation Success: {yaml_result['success']}")
            print(f"   Services: {yaml_result['servicesCount']}")
            print(f"   Activities: {yaml_result['activitiesCount']}")
            if yaml_result['yamlContent']:
                print("   YAML Preview (first 500 chars):")
                print(f"   {yaml_result['yamlContent'][:500]}...")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n🎯 GraphQL Schema Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_graphql_queries())
