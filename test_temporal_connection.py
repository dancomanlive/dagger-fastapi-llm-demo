#!/usr/bin/env python3
"""
Simple test to verify Temporal connection.
"""
import asyncio
from temporalio.client import Client

async def test_connection():
    print("Attempting to connect to Temporal...")
    try:
        client = await Client.connect('localhost:7233')
        print('✅ Successfully connected to Temporal!')
        
        # Try to list workflows
        async for workflow in client.list_workflows():
            print(f"Found workflow: {workflow.id}")
            break
        else:
            print("No workflows found")
            
        await client.close()
        print("Connection closed successfully")
    except Exception as e:
        print(f'❌ Connection failed: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection())
