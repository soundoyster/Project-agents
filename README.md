# Multi-Agent Data Analysis & Visualization System

This project implements an **Agentic Workflow** using **Semantic Kernel**. It features a team of AI agents that collaborate to clean raw data, perform statistical analysis, visualize results, and generate a comprehensive final report.

## 🚀 Overview

The system uses a group of specialized agents to process data through several stages:
1.  **Data Cleaning**: Identifying and removing outliers.
2.  **Statistical Analysis**: Calculating key metrics.
3.  **Human-in-the-Loop**: Asking for user approval or feedback before proceeding.
4.  **Automated Visualization**: Generating Python code to plot the results.
5.  **Report Generation**: Synthesizing all logs and artifacts into a professional Markdown report.

---

## 🛠️ Prerequisites

* Python 3.10 or higher.
* An Azure OpenAI account with a deployed GPT-4 model.
* The necessary libraries installed are in requirementes.txt:
    ```bash
    pip install -r requirements.txt
    ```

---

## ⚙️ Configuration

Before running the project, you must configure your environment variables:

1.  Locate the file named `.env.template` in the root directory.
2.  Open it and add your Azure OpenAI credentials.
3.  **Rename** the file to `.env`.

> **Note:** The `.env` file is ignored by git to keep your credentials secure.

---

## 🏃 How to Run

To start the agentic workflow, simply execute the main script from your terminal:

```bash
python final.py
