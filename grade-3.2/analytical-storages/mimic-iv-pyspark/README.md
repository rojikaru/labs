# MIMIC-IV PySpark Analysis project

This project is a data analysis and machine learning project that uses the MIMIC-IV dataset and Apache Spark via PySpark. The project is structured to allow for scalable data processing and analysis, leveraging the power of Spark for handling large datasets.

## Dataset

The MIMIC-IV dataset is a large, publicly available dataset of de-identified health-related data associated with over 40,000 critical care patients. It includes a wide range of data types, such as demographics, vital signs, laboratory results, medications, and more. The dataset is hosted on [PhysioNet](https://physionet.org/content/mimiciv/3.1/) and requires registration to access.

## Requirements

- Python 3.14 or higher
- Apache Spark (via [PySpark](https://pypi.org/project/pyspark/) ≥ 4.1.1)
- Java 17 (see [Java Installation](#java-installation) below)
- [uv](https://docs.astral.sh/uv/) — fast Python package and project manager
- Key Python dependencies (managed by `uv`):
  - `pyspark` — distributed data processing
  - `polars` — local data manipulation

## Installation

To set up the project, follow these steps:

1. Clone the repository:

    ```bash
    git clone git@github.com:rojikaru/mimic-iv-pyspark.git
    cd mimic-iv-pyspark
    ```

2. Install [uv project manager](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer) and project dependencies:

    ```bash
    pip install uv
    ```

3. Set up a virtual environment and activate it:

    ```bash
    uv venv
    source .venv/bin/activate # On Windows, use .venv\Scripts\activate
    ```

4. Install the project dependencies:

    ```bash
    uv sync
    ```

5. Download the MIMIC-IV dataset from the [MIMIC-IV](https://physionet.org/content/mimiciv/3.1/) website and place the files in the `artifacts/` directory.

### Java Installation

Java 17 is required to run Apache Spark. You can install it manually or use [mise](https://mise.jdx.dev/) for automatic version management:

```bash
# Install mise (see https://mise.jdx.dev/getting-started.html)
mise install   # reads .java-version / mise.toml and installs Java 17 automatically
```

Alternatively, install Java 17 directly from [Eclipse Temurin](https://adoptium.net/) or your OS package manager.

## Usage

Local execution:

```bash
uv run -m src.main
```

Via Docker:

```bash
# Build the Docker image
docker build -t mimic-iv-pyspark .

# Grant permissions to the results directory
mkdir -p artifacts/results && sudo chmod o+w artifacts/results

# Execute (Linux / macOS)
docker run -v $(pwd)/artifacts:/app/artifacts -v $(pwd)/artifacts/results:/app/artifacts/results mimic-iv-pyspark

# Execute (Windows PowerShell)
docker run -v ${PWD}/artifacts:/app/artifacts -v ${PWD}/artifacts/results:/app/artifacts/results mimic-iv-pyspark
```

## License

Please see the [UNLICENSE](UNLICENSE) file for details on the license for this project.
