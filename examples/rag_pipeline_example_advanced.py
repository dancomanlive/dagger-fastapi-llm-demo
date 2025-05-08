"""
Example usage of the RAG pipeline with Superlinked + Qdrant.
"""
import json
import asyncio
import dagger

from pipelines.rag_pipeline import ingest_document, query_rag

async def main():
    # Connect to Dagger
    async with dagger.Connection() as client:
        print("Connected to Dagger")
        
        # Define document data
        document_text = """
# Renewable Energy Sources

## Solar Energy

Solar energy is radiant light and heat from the Sun that is harnessed using a range of technologies such as solar power to generate electricity, solar thermal energy (including solar water heating), and solar architecture.

It is an essential source of renewable energy, and its technologies are broadly characterized as either passive solar or active solar depending on how they capture and distribute solar energy or convert it into solar power.

### Photovoltaic Technology

Photovoltaic (PV) cells convert light into electricity. They are made of semiconducting materials similar to those used in computer chips. When these materials absorb sunlight, the solar energy knocks electrons loose from their atoms, allowing the electrons to flow through the material to produce electricity.

## Wind Energy

Wind power or wind energy is the use of wind to provide mechanical power through wind turbines to turn electric generators for electrical power. Wind power is a popular sustainable, renewable source of power that has a much smaller impact on the environment compared to burning fossil fuels.

### Wind Turbines

Wind turbines operate on a simple principle. The energy in the wind turns two or three propeller-like blades around a rotor. The rotor is connected to the main shaft, which spins a generator to create electricity.

## Hydroelectric Energy

Hydroelectric energy, also called hydroelectric power or hydroelectricity, is a form of energy that harnesses the power of water in motion—such as water flowing over a waterfall—to generate electricity.

### Dams and Reservoirs

Most hydroelectric power plants have a reservoir of water, a gate or valve to control how much water flows out of the reservoir, and an outlet or place where the water ends up after flowing through the turbine.
        """
        
        document_id = "renewable_energy_101"
        project_id = "test_project"
        index_name = "energy_documents"
        
        # Step 1: Ingest document
        print(f"Ingesting document: {document_id}")
        ingest_result = await ingest_document(
            client=client,
            text=document_text,
            document_id=document_id,
            project_id=project_id,
            index_name=index_name,
            chunk_size=400,
            overlap=100,
            respect_sections=True,
            metadata={
                "title": "Renewable Energy Overview",
                "author": "Energy Expert",
                "category": "educational",
                "date": "2025-05-01"
            }
        )
        
        print("Ingestion result:")
        print(json.dumps(ingest_result, indent=2))
        
        # Step 2: Query the RAG system
        test_queries = [
            "What is solar energy and how does it work?",
            "Tell me about wind turbines and how they generate electricity",
            "I'm looking for information about hydroelectric dams",
            "Which renewable energy source uses photovoltaic technology?"
        ]
        
        for i, query in enumerate(test_queries):
            print(f"\nQuery {i+1}: {query}")
            query_result = await query_rag(
                client=client,
                query=query,
                project_id=project_id,
                index_name=index_name,
                use_nlq=True,
                weights={"vector": 0.8, "keyword": 0.2},
                limit=3,
                model="gpt-4o-mini"
            )
            
            print("Response:")
            print(query_result.get("response", "No response generated"))
            
            print("\nCitations:")
            for citation in query_result.get("citations", []):
                print(f"- {citation}")
            
            print("\n" + "-"*80)

if __name__ == "__main__":
    asyncio.run(main())
