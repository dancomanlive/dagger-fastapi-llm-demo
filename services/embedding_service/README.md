# Embedding Service

This project implements a document embedding and indexing service using FastAPI. It provides API endpoints for indexing documents and checking the health of the service, utilizing Qdrant for vector storage and handling document processing.

## Project Structure

```
embedding_service
├── main.py          # Implements the FastAPI application and API endpoints
├── Dockerfile       # Contains instructions to build the Docker image
├── requirements.txt # Lists the Python dependencies required for the project
└── README.md        # Documentation for the project
```

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd embedding_service
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the root directory with the following variables:
   ```
   QDRANT_HOST_FOR_SERVICE=http://localhost:6333
   QDRANT_API_KEY=your_api_key
   EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   PAYLOAD_TEXT_FIELD_NAME=document
   ```

## Running the Service

To run the FastAPI application, execute the following command:
```bash
uvicorn main:app --reload
```

The service will be available at `http://localhost:8000`.

## API Endpoints

- **Index Documents**
  - **Endpoint:** `POST /index`
  - **Description:** Indexes a list of documents into the specified Qdrant collection.
  - **Request Body:**
    ```json
    {
      "collection": "your_collection_name",
      "documents": [
        {
          "id": "unique_document_id",
          "text": "Your document text",
          "metadata": {}
        }
      ],
      "create_collection": true
    }
    ```

- **Health Check**
  - **Endpoint:** `GET /health`
  - **Description:** Checks the health of the embedding service and Qdrant connection.

## Docker

To build and run the Docker container, use the following commands:

1. **Build the Docker image:**
   ```bash
   docker build -t embedding_service .
   ```

2. **Run the Docker container:**
   ```bash
   docker run -p 8000:8000 embedding_service
   ```

## License

This project is licensed under the MIT License. See the LICENSE file for more details.