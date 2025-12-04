# AI Document Assistant  
*A modular AI service for answering student questions using university documents.*

##  Overview  
The **AI Document Assistant** is a lightweight backend service designed to help students quickly find information from university documents. It provides instant answers to questions normally buried inside long PDF documents 
It supports documents such as:

- Student Handbooks (UG / PGT / PGR)
- Academic Integrity Regulations
- Support guides, policies, or any additional PDFs

The system works **locally** or in the **cloud (AWS Fargate)**.

---

## How It Works
A full worked example is available in the tutorial notebook:[View the tutorial notebook](doc/tutorial.ipynb)
### **1. PDF Processing**
- Extracts text from university PDF documents.
- Saves cleaned text **locally** and/or **on AWS S3**.
- Only needs to run when documents are updated.

### **2. AI Question Classification**
Uses openAI to determine which document a question refers to (e.g., `handbook`, `academic_integrity`, or any new category added).

### **3. Endpoint Routing**
Each document type has a dedicated endpoint.  
The classifier automatically selects the correct one.

### **4. Retrieval-Augmented Generation (RAG)**
- Documents are embedded using OpenAI embeddings.
- Stored in a ChromaDB vector store.
- Relevant text is retrieved and used to produce a grounded answer.

### **5. In-Memory Q&A History**
Stores a short session history keyed by user token.

---
## How to run the service
### Configuration (`.env` File)

A [template file]`.env.example` is included in the repository.


#### 1. Create a copy of the template

```bash
cp .env.example .env
```

#### 2. Fill in the required values

Replace placeholder values and provide your openAI API key.



The service can run in two modes:

1. **Local Mode** — for development/testing
2. **AWS Mode** — for using the deployed service on AWS Fargate

Your `.env` file determines which endpoint the tutorial will call:

- If `MODE="development"` → uses `IP_LOCAL`
- If `MODE="production"` → uses `IP_AWS`

---

### 1. Local Mode (Development)

#### Install environment

```bash
poetry install
poetry shell
```

#### Process the PDFs (one-time step)

```python
process_all_handbooks(levels="pgr")
process_other_document(type="academic-integrity")
```

#### Start the API locally

```bash
uvicorn app.api.main:app --reload --port 8080
```

The service will be available at:

```
http://localhost:8080
```

#### Use the API

[View the tutorial notebook:](doc/tutorial.ipynb) , in which you can:

- Do health check
- Enter questions
- Classify questions
- Call `ask_<category>` endpoints
- View sources & history

---

### 2. AWS Mode (Production)

You can call it the same way, but the `.env` selects the AWS IP instead.
Simply rerun the tutorial or make the same requests, and they will be sent to AWS.



## API Usage Examples

**curl:**

### 1. Handbook Query

```bash
curl -X POST http://localhost:8080/ask_academic_integrity \
  -H "Content-Type: application/json" \
  -d '{"question":"How long can I be registered for a PhD?","level":"pgr"}'
```

### 2. Academic Integrity Query

```bash
curl -X POST http://localhost:8080/academic-integrity \
  -H "Content-Type: application/json" \
  -d '{"question":"How is plagiarism detected in theses?"}'
```