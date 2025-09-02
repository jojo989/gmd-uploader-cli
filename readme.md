# GMD Uploader CLI ##### [https://wyliemaster.github.io/](https://wyliemaster.github.io/gddocs)

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

## Game version table

| Client version | Ingame version |
| -------------- | -------------- |
| 1              | 1.0            |
| 2              | 1.1            |
| 3              | 1.2            |
| 4              | 1.3            |
| 5              | 1.4            |
| 6              | 1.5            |
| 7              | 1.6            |
| 10             | 1.7            |
| 18             | 1.8            |
| 19             | 1.9            |
| 20             | 2.0            |
| 21             | 2.1            |
| 22             | 2.2            |


## common errors
### GD Servers errors
- If ```-n``` includes words that are on RobTop's blacklist, the upload will fail
- If ```-n``` includes symbols, the upload will fail
- If ```--gameversion``` is higher than 22, the upload will fail as of writing this (for obvious reasons)
- If ```--levelversion``` is higher than 127, it will default to 127 since it's the max
### script errors
- .gmd2 / .lvl files are not supported. Parsing of such files will fail. (suport will be added later)
