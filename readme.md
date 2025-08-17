# GMD Uploader CLI

A command-line interface (CLI) tool for uploading Geometry Dash levels directly from a `.gmd` file to the official servers.

## Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/jojo989/gmd-uploader-cli.git
    ```

2.  **Navigate to the project directory:**
    ```sh
    cd gmd-uploader-cli
    ```

3.  **Install the required dependencies:**
    This project requires Python 3.
    ```sh
    pip install -r requirements.txt
    ```

## Usage

You can run the script from your terminal using `python main.py` with the appropriate arguments.

### Basic Example

To upload the infamous level "Element 111 rg" from a file named `level.gmd`:

```sh
python main.py \
    --username YourUsername \
    --password YourPassword \
    --levelname "Element 111 rg" \
    --gmd path/to/level.gmd \
    --description "This is a test level."
```

If successful, the script will print the new Level ID.

### Game version table

wip uwu
