

---

# ⚖️ LLM-Powered Legal Knowledge Graphs for Indian Courts
 **Ontology-driven. LLM-boosted. Graph-native.**  
Creating the future of legal intelligence, one node at a time.

---


# 🚧 Project Status: Work In Progress
This project is currently under active development.

🧪 Expect rapid changes, restructuring, and experimental branches.

🧠 We're still refining prompt engineering, triple extraction accuracy, and ontology alignment.

🧵 The codebase will grow to support:

High Court + Tribunal integration

Vector-based case retrieval

GraphRAG-powered legal QA

Timeline, Bench, Provision, and Citation mapping

We welcome early feedback, issues, and pull requests — but be advised that the API and structure may change frequently.
## 🧠 Project Overview

This project aims to **build ontology-aligned Knowledge Graphs (KGs)** for the **Supreme Court of India** by extracting structured information from legal judgments using **Large Language Models (LLMs)**.

It leverages:
- A curated legal ontology (from NyOn)
- Neo4j graph database
- LLM pipelines (for entity/relation extraction)
- Vector search for retrieval
- Graph Reasoning (GraphRAG/Knowledge-augmented NLP)

> 🧬 The ultimate goal:  
> To build a foundation for AI-assisted **legal research**, **argument mining**, and **decision reasoning** in the Indian legal system.

---

## 📚 Table of Contents

- [🧠 Project Overview](#-project-overview)
- [📦 Requirements](#-requirements)
- [🛠️ Installation & Setup](#️-installation--setup)
- [🚀 Usage](#-usage)
- [🧩 Sample Queries](#-sample-queries)
- [📐 Ontology Acknowledgement](#-ontology-acknowledgement)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## 📦 Requirements

To run this project locally, make sure you have the following:

- **Python 3.10+**
- **Neo4j 5.11+** (with vector index support)
- **Neo4j APOC** plugin installed
- **OpenAI or HuggingFace API key** (for LLM-based extraction)
- `requirements.txt` includes:
  - `neo4j`
  - `openai`
  - `langchain`
  - `langchain-community`
  - `langchain-core`
  - `langchain-experimental`
  - `langchain-google-gena`
  - `langchain-huggingfac`
  - `langchain-neo4`
  - `langchain-openai`
  - `langchain-text-splitter`
  - `tqdm`
  - `pydantic`
  - `python-dotenv`

```bash
pip install -r requirements.txt
````

---

## 🛠️ Installation & Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/jahab/OntoLogyBasedKGCreation.git
   cd OntoLogyBasedKGCreation
   ```

2. **Configure `.env`**
   Create a `.env` file with:

   ```
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=admin@123
   OPENAI_API_KEY=sk-...
   GOOGLE_API_KEY=GI...
   HF_TOKEN=hf_...
   ```
3. Install docker compose cli

3. Run ```docker compose up --build ```
---

## 🚀 Usage
**(WIP with UI)**

### Services
- **Neo4j Browser:** [http://localhost:7474/browser/preview](http://localhost:7474/browser/preview)  
- **Qdrant Dashboard:** [http://localhost:6333](http://localhost:6333)  
- **Graph API Endpoint:** [http://0.0.0.0:4044/](http://0.0.0.0:4044/)  

---

### 🔹 Create Graph
**Endpoint:**  
```http
POST http://0.0.0.0:4044/create_graph
# Request Body
{
  "pdf_file": "35346_2009_39_1501_24473_Judgement_29-Oct-2020.pdf",
  "model_provider": "google",
  "embedding_provider": "google",
  "embedding_model": "models/text-embedding-004",
  "extraction_model": "gemini-2.5-flash"
}

# Response Body
{"task_id":"3d1fb599-38bf-4945-8a67-49eac7aad4d6"}
```
### 🔹 Check Graph Creation Status
**Endpoint:**  
```http
POST http://0.0.0.0:4044/status

# Request Body
{
  "task_id": "3d1fb599-38bf-4945-8a67-49eac7aad4d6"
}
```
 ---

## 📐 Ontology Acknowledgement

This project is **powered by the excellent [NyOn ontology](https://github.com/semintelligence/NyOn)**
Developed by [semintelligence](https://github.com/semintelligence), NyOn provides a structured legal schema to represent core legal concepts such as:

* `CourtCase`, `Court`, `Judge`, `Decision`, `LegalProvision`, `Bench`, `Party`, and more.

We are deeply grateful for their contribution to the open legal knowledge ecosystem. 🙏

---

## 🤝 Contributing

Want to shape the future of legal AI in India?
We welcome contributions in the form of:

* Ontology extensions
* New entity extractors
* Fine-tuned LLMs
* RAG pipelines
* Legal document parsers

Feel free to submit a PR or open an issue!

---

## 📄 License

GNU GENERAL PUBLIC LICENSE

---

## 🚀 Vision

> **Build a legal co-pilot for India.**
> Assist lawyers, judges, researchers, and policy makers with deep insights, structured search, and AI-powered reasoning.

Stay tuned for High Court expansion, timeline visualizations, and ChatRAG integrations. 🧾🔍⚖️

---

