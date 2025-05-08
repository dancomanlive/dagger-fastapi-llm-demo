# 📡 API Usage

This document provides detailed information about the available API endpoints and how to use them.

## Available Endpoints

### `GET /hello`

Get a simple greeting from a container.

#### Example Request:

```bash
# Default greeting
curl -X GET http://localhost:8000/hello

# Custom name
curl -X GET "http://localhost:8000/hello?name=Dan"
```

#### Example Response:

```json
{
  "message": "Hello, Dan!"
}
```

### `POST /chat`

Send a prompt to the OpenAI model and get a response.

#### Example Request:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is the capital of China?"}'
```

#### Example Response:

```json
{
  "response": "The capital of China is Beijing."
}
```

You can optionally pass a specific model:

```json
{
  "prompt": "Hello!",
  "model": "gpt-4"
}
```

### `POST /process`

Process data using a container.

#### Example Request:

```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"name": "dan", "message": "hello"}'
```

#### Example Response:

```json
{
  "result": {
    "NAME": "DAN",
    "MESSAGE": "HELLO"
  }
}
```

### `POST /analyze-text`

Analyze text and get statistics.

#### Example Request:

```bash
curl -X POST http://localhost:8000/analyze-text \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a sample text for analysis. This sample contains repeated words."}'
```

#### Example Response:

```json
{
  "analysis": {
    "word_count": 12,
    "character_count": 69,
    "most_common_words": {
      "this": 2,
      "sample": 2,
      "is": 1,
      "a": 1,
      "text": 1
    },
    "average_word_length": 4.75
  }
}
```

### `POST /filter-csv`

Filter CSV data based on column values.

#### Example Request:

```bash
curl -X POST http://localhost:8000/filter-csv \
  -H "Content-Type: application/json" \
  -d '{
    "csv_data": "id,name,department,salary\n1,John,Engineering,75000\n2,Alice,Marketing,65000\n3,Bob,Engineering,80000\n4,Carol,HR,60000",
    "column": "department",
    "value": "Engineering"
  }'
```

#### Example Response:

```json
{
  "result": {
    "filtered_csv": "id,name,department,salary\n1,John,Engineering,75000\n3,Bob,Engineering,80000\n",
    "rows": [
      {
        "id": "1",
        "name": "John",
        "department": "Engineering",
        "salary": "75000"
      },
      {
        "id": "3",
        "name": "Bob",
        "department": "Engineering",
        "salary": "80000"
      }
    ],
    "count": 2
  }
}
```
