# Ciena saos6 to saos10 converter

## Running the Converter on Github Codespaces

1. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

2. Add your input files to the `saos6-configs` directory.

3. Run the conversion script:
    ```sh
    ./index.py   # or python index.py
    ```

## Output

- The converted files will be saved in the `output/xml` and `output/saos10` directories.
- CSV files will be generated in the `app/assets` directory.
