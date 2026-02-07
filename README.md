# IronTrust Analytics

**IronTrust Analytics** is a web-based dashboard for DNS query analytics. It provides insight into query volume, entropy, NXDOMAIN ratios, and other key performance indicators (KPIs) to help monitor and detect unusual DNS behavior.

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- Overview KPIs: Total Queries, Unique QNAMEs, Root Domains, Source IPs
- Risk KPIs: High-entropy queries, NXDOMAIN ratio
- Distribution charts: QName entropy, Subdomain entropy
- Top-N charts: Top QNAMEs, Top Root Domains, High-entropy QNAMEs
- RCODE and Query Type breakdowns
- Responsive, modern UI with React + Plotly

---

## Project Structure

.
├── apps
│ ├── web # Frontend web application (React + TypeScript)
│ └── notebooks # Analysis notebooks (excluded from GitHub)
├── data # Raw/processed data (excluded from GitHub)
├── jobs # ETL / serverless jobs
├── libs # Shared Python libraries
├── services # Backend services (API, parser)
├── infra # Infrastructure / Terraform scripts
└── td.json # Project metadata