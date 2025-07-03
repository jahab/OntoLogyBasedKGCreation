

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
- [⚙️ Core Components](#️-core-components)
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
   NEO4J_PASSWORD=your_password
   OPENAI_API_KEY=sk-...
   GOOGLE_API_KEY=GI...
   ```

3. **Start Neo4j**
   Make sure Neo4j is running locally with the appropriate plugins (APOC and vector indexing enabled).

4. **Import Ontology**
   The base ontology is used to guide the KG structure. You can import it using:

   ```cypher
   CALL n10s.onto.import.fetch("https://raw.githubusercontent.com/semintelligence/NyOn/main/NyOn.owl", "RDF/XML")
   ```

---

## ⚙️ Core Components

| Module             | Purpose                                                                                    |
| ------------------ | ------------------------------------------------------------------------------------------ |
| `app.py`           | Main pipeline to load extracted nodes and relationships into Neo4j from LLM-generated JSON |
| `output_parser.py` | Parses raw LLM outputs into ontology-aligned triples and cleans metadata                   |
| `utils.py`         | Utility functions for label management, Cypher generation, and Neo4j connection handling   |
| `prompts.py`       | Stores and manages prompt templates for LLMs, tailored for legal triple extraction         |


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

MIT License — feel free to fork, extend, and build upon it.

---

## 🚀 Vision

> **Build a legal co-pilot for India.**
> Assist lawyers, judges, researchers, and policy makers with deep insights, structured search, and AI-powered reasoning.

Stay tuned for High Court expansion, timeline visualizations, and ChatRAG integrations. 🧾🔍⚖️

---

