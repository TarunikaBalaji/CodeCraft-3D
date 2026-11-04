# CODECRAFT 3D
### BUILD. BREAK. VERIFY. REBUILD.

**An Evidence-Driven AI Engineering Simulator for Real-World Building Challenges**

CODECRAFT 3D transforms complex building regulations into interactive engineering challenges. It combines AI-powered regulation extraction, evidence traceability, deterministic engineering calculations and 3D building simulation in a gamified environment.

Instead of simply reading building regulations, users can explore how those regulations affect a building, experiment with design decisions, identify potential violations and improve their designs through interactive challenges.

---

## 1. The Problem

Building regulations contain important requirements governing setbacks, building height, site coverage and other construction parameters.

However, translating lengthy regulatory documents into practical design decisions can be challenging.

- Important constraints are scattered across lengthy documents.
- Understanding how one design decision affects other requirements is difficult.
- Identifying potential conflicts requires careful interpretation and calculations.
- Traditional document-based workflows do not provide an engaging way to experiment with building designs.

**The gap:** There is a need for an interactive environment that connects regulatory information with practical engineering decisions.

## 2. Our Solution

CODECRAFT 3D introduces a game-based engineering simulator where users can explore building design challenges and understand the consequences of their decisions.

The platform combines:

- AI-assisted extraction of building regulation requirements.
- Evidence-based validation of extracted information.
- Deterministic calculations for building geometry and constraints.
- Interactive 3D building visualization.
- Gamified missions, rewards and progression.

The objective is to make engineering constraints understandable, interactive and actionable.

## 3. How CODECRAFT 3D Works

### BUILD → BREAK → VERIFY → REBUILD

**BUILD**

Users explore the 3D environment and configure building parameters such as dimensions, height and setbacks.

**BREAK**

Users experiment with design modifications and discover how changing parameters can introduce potential engineering violations.

**VERIFY**

The system evaluates supported design constraints using deterministic calculations and displays the resulting feedback.

**REBUILD**

Users refine their designs, address detected issues and work towards a better configuration.

This creates an interactive learning experience rather than a passive document-reading workflow.

## 4. Key Innovations

### 4.1 Regulation Intelligence

Muse Spark assists in extracting candidate building requirements from uploaded regulatory PDFs.

The extracted information is treated as candidate data rather than automatically accepted as legally applicable requirements.

### 4.2 Evidence Traceability

The evidence validation layer checks whether extracted requirements can be traced to their cited document pages and supporting excerpts, including relevant numerical values and units.

This helps users inspect where a candidate requirement originated.

### 4.3 Deterministic Engineering Evaluation

The geometry engine evaluates supported parameters such as:

- Building dimensions
- Setback distances
- Building height
- Site coverage

It identifies potential violations based on the configured constraints and calculation rules.

### 4.4 Interactive 3D Simulation

Users can explore and modify building configurations in a visual environment, making engineering decisions easier to understand.

### 4.5 Gamified Engineering Experience

CODECRAFT 3D incorporates missions, experience points, ranks, rewards and challenges to make engineering exploration more engaging.

### 4.6 Dependency and Change-Impact Intelligence

The project includes regulation dependency and change-impact modules designed to represent relationships between constraints and compare the consequences of design changes.

These modules provide a foundation for more advanced cascading impact analysis.

---

## 5. What Makes It Different?

| Traditional workflow | CODECRAFT 3D |
|---|---|
| Read lengthy regulations | Explore extracted candidate requirements |
| Interpret requirements manually | Inspect document-linked evidence |
| Calculate design constraints separately | Evaluate supported constraints through deterministic calculations |
| Review designs statically | Explore interactive 3D configurations |
| Learn through documentation | Learn through missions and challenges |

**Our central idea:** Make building regulations something users can interact with, experiment against and understand through simulation.

## 6. Meta Muse Spark Integration

Muse Spark is integrated into the regulation intelligence workflow.

It assists in processing uploaded building regulation documents and extracting candidate requirements that can subsequently undergo evidence validation.

The architecture separates AI-assisted extraction from deterministic verification and engineering evaluation.

This distinction is important: AI-generated candidate requirements do not automatically become approved design constraints.

**Meta Model API credits:** CODECRAFT 3D used $149.66 of the $150 in credits offered through the hackathon.

## 7. How to Run CODECRAFT 3D

### Prerequisites

- Python 3.10 or later
- Git
- VS Code or another Python editor
- Internet access for installing dependencies

### Step 1: Clone the repository

Open a terminal and execute:

```bash
git clone https://github.com/TarunikaBalaji/CodeCraft-3D.git
cd CodeCraft-3D
```

### Step 2: Create a virtual environment

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

If using Git Bash:

```bash
source .venv/Scripts/activate
```

### Step 3: Install dependencies

```bash
python -m pip install --upgrade pip
pip install streamlit plotly networkx pydantic pymupdf requests python-dotenv
```

### Step 4: Configure Muse Spark API access (optional)

The interactive game environment can be explored without configuring the API key.

To enable live regulation analysis, create a `.env` file in the project root:

```env
MODEL_API_KEY=your_meta_model_api_key
```

Use a valid API key with the required access and billing configuration.

**Important:** Do not upload your `.env` file or expose your API key in the repository.

### Step 5: Launch the application

From the project root:

```bash
streamlit run app.py
```

### Step 6: Open the application

Streamlit will provide a local URL. Open:

```text
http://localhost:8501
```

You can now explore the CODECRAFT 3D environment.

---

## 8. Suggested Judge Walkthrough

For the best understanding of the project, we recommend this sequence:

1. **Explore the environment:** Open CODECRAFT 3D and understand the interactive engineering simulator.
2. **Explore building design:** Experiment with available building parameters and observe the 3D representation.
3. **Trigger design challenges:** Modify supported parameters and observe the engineering evaluation.
4. **Explore gamification:** Experience missions, XP, ranks and progression.
5. **Explore regulation intelligence:** If API access is configured, upload a supported building regulation PDF and inspect the extracted candidate requirements and their evidence.
6. **Review the engineering feedback:** Observe how supported constraints are evaluated.

The regulation analysis workflow requires a configured Muse Spark API key. The core simulator can be explored without it.

## 9.Future Scope

CODECRAFT 3D is an experimental engineering and educational prototype.

- Live constraint ripple simulation across dependent building parameters.
- More advanced regulatory dependency and conflict analysis.
- OCR support for scanned regulatory documents.
- Broader engineering calculations and additional building standards.
- More interactive missions and increasingly complex design challenges.
- Improved evidence-linked explanations for engineering decisions.

**Disclaimer:** CODECRAFT 3D is not an official building approval system, legal interpretation service or certified building-code compliance tool. Its outputs must not replace qualified engineering review or official regulatory verification.

## 10. Project Vision

We envision a future where complex engineering regulations are not merely documents to interpret, but interactive systems that people can explore, understand and use to make better-informed design decisions.

CODECRAFT 3D brings together AI, evidence traceability, engineering logic, 3D simulation and gamification to move towards that vision.

### Repository

[GitHub – CODECRAFT 3D](https://github.com/TarunikaBalaji/CodeCraft-3D)

**CODECRAFT 3D — BUILD. BREAK. VERIFY. REBUILD.**
