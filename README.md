# saos6-saos10-converter

## Setup and Run in Codespaces

### Prerequisites

Ensure you have the following installed:
- Python 3.8 or higher
- pip (Python package installer)

### Setup

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/saos6-saos10-converter.git
    cd saos6-saos10-converter
    ```

2. Create and activate a virtual environment:
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

### Running the Converter

1. Ensure you have the necessary input files in the `saos6-configs` directory.

2. Run the conversion script:
    ```sh
    python index.py
    ```

### Running in Codespaces

1. Open the repository in GitHub Codespaces.

2. Follow the setup steps to create a virtual environment and install dependencies.

3. Run the conversion script:
    ```sh
    python index.py
    ```

### Additional Information

- The converted files will be saved in the `output/xml` and `output/saos10` directories.
- CSV files will be generated in the `app/assets` directory.
