# CCA Project — Certificate Viewer By Hardik

A web-based **SSL/TLS Certificate Aggregation and Certificate Authority (CA) Analysis Platform** built with Python, FastAPI, and MongoDB.

The CCA Project collects SSL/TLS certificate information from `gov.in` domains, stores certificate and Certificate Authority data in MongoDB, combines the datasets, and provides a web interface for viewing certificate and CA details.

## 📌 Overview

The project is designed to simplify the collection, processing, storage, and visualization of SSL/TLS certificate information.

It can:

- Aggregate SSL/TLS certificate data
- Store certificate metadata in MongoDB
- Collect Certificate Authority information
- Merge certificate and CA information
- Provide a web-based certificate viewer
- Support large-scale certificate collection using multithreading

## 🎯 Who Is This For?

This project can be useful for:

- 🔐 Cybersecurity researchers
- 🛡️ Security analysts
- 👨‍💻 Developers working with TLS/SSL
- 🎓 Cybersecurity and computer science students
- 🔎 Certificate and PKI researchers
- 🏢 Organizations performing certificate inventory and analysis


## 🏗️ Architecture

```text
                    ┌─────────────────────┐
                    │      Web Client     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       FastAPI       │
                    │      Backend        │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
             ┌─────────────┐      ┌───────────────┐
             │   certdb    │      │ cert_scanner  │
             │             │      │               │
             │ Certificates│      │  CA / Root CA │
             └─────────────┘      └───────────────┘
                    │                     │
                    └──────────┬──────────┘
                               ▼
                     ┌──────────────────┐
                     │ Combined Dataset │
                     └────────┬─────────┘
                              │
                              ▼
                     ┌──────────────────┐
                     │ Jinja2 Templates │
                     │   HTML / CSS /   │
                     │   JavaScript     │
                     └──────────────────┘
```

## ⚙️ How It Works

1. Collect target domains.
2. Fetch SSL/TLS certificates from the domains.
3. Extract certificate metadata.
4. Store certificate information in MongoDB.
5. Retrieve certificate-chain and CA information.
6. Store CA information in a separate MongoDB database.
7. Normalize domain names.
8. Combine certificate and CA records.
9. Render the processed information through the web interface.

## 🗄️ Database Structure

The project uses MongoDB with two databases.

### `certdb`

Stores main certificate records:

```text
certdb
└── certificates
    ├── domain
    ├── subject
    ├── issuer
    ├── valid_from
    ├── valid_to
    ├── certificate
    └── public_key
```

### `cert_scanner`

Stores Certificate Authority and certificate-chain information:

```text
cert_scanner
└── certificates
    ├── domain
    ├── leaf
    ├── intermediates
    ├── root
    ├── error
    └── scanned_at
```

Certificate and CA information are logically joined using the domain name.

## 📁 Project Structure

```text
CCA-Project-main/
│
├── main.py
├── requirements.txt
├── domains.txt
│
├── dedupe_certs.py
├── backfill_ca_id.py
├── domain scrapper.py
├── fetching 10000 main.py
├── root ca 10000 +database test.py
│
├── templates/
│   ├── index.html
│   └── index2.html
│
├── static/
│   ├── style.css
│   ├── style2.css
│   ├── script.js
│   ├── script2.js
│   ├── coding.jpg
│   └── icon.jpg
│
└── .vscode/
    └── settings.json
```

## 🧰 Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| FastAPI | Backend web framework |
| MongoDB | Certificate and CA data storage |
| Jinja2 | HTML template rendering |
| HTML | Web interface |
| CSS | Styling |
| JavaScript | Frontend functionality |
| Uvicorn | Application server |
| `cryptography` | X.509 certificate processing |
| `pymongo` | MongoDB integration |
| BeautifulSoup | Domain scraping |

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/hardik1106-code/CCA-Project.git
cd CCA-Project
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

**Windows**

```bash
venv\Scripts\activate
```

**Linux/macOS**

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure MongoDB

Create a `.env` file in the project root:

```env
MONGOURL=your_mongodb_connection_string
```

### 5. Start the application

```bash
python -m uvicorn main:app --reload
```

Then open:

```text
http://127.0.0.1:8000
```

## 🔎 Data Collection

The repository contains supporting scripts for certificate and domain collection:

| Script | Purpose |
|---|---|
| `domain scrapper.py` | Collects domains |
| `dedupe_certs.py` | Remove Duplicate Certificates |
| `backfill_ca_id.py` | Fetches CA ID |
| `fetching 10000 main.py` | Large-scale certificate fetching |
| `root ca 10000 +database test.py` | Root CA and certificate-chain processing |

Certificate collection uses TLS connections to retrieve certificates and Python's `cryptography` library to parse X.509 certificate data.

For larger collections, the project uses `ThreadPoolExecutor` to perform certificate processing concurrently.

## 🧹 Data Normalization

The project normalizes domain information by:

- Converting domains to lowercase
- Removing unnecessary whitespace
- Removing redundant fields
- Formatting data into structured JSON

Example:

```python
domain = (cert.get("domain") or "").strip().lower()
```

## 🌐 Web Interface

The frontend uses server-side rendering with Jinja2.

```text
/          → Homepage
/gov.in    → Certificate display page
```

The certificate display page retrieves processed certificate information and renders certificate authority details.

## 🔒 Security

The current project security architecture includes:

- Environment variables for configuration
- Controlled MongoDB access

> **Note:** Additional security controls may be required before deploying the application publicly.

## 📊 Project Purpose

The CCA Project provides a foundation for collecting and analyzing SSL/TLS certificate information at scale.

By combining certificate records with CA and certificate-chain information, the platform can help users investigate:

- Certificate issuers
- Certificate validity
- Public keys
- Certificate chains
- Root CAs
- CA relationships
- Domain certificate inventories

## 🔗 Repository

https://github.com/hardik1106-code/CCA-Project

---

**CCA Project — Certificate Viewer**

*A foundation for SSL/TLS certificate intelligence and cybersecurity analytics.*
