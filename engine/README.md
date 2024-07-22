# Search Engine

## Usage

- To crawl pages, you need to run the following command:

   ```
   python main.py --online
   ```
- Run the following command to start the server:

   ```
   python server.py
   ```

- Open your browser and navigate to `http://localhost:8000/` to view the application.

## Requirements

- `Python 3`
- `pip`
- `virtualenv`

## Installation

1. **Install Python 3:**

- Download and install the latest version of Python 3 from the official website.

2. **Install virtualenv:**

- Open a terminal and run the following command:

   ```
   pip install virtualenv
   ```

3. **Create a virtual environment:**

- Create the virtual environment:

  ```
  virtualenv --python=3.11 .venv
  ```

- Activate the virtual environment:

  ```
  source .venv/bin/activate
  ```

4. **Install requirements:**

- Ensure you have a requirements.txt file in your project directory.
- Run the following command to install the dependencies:

   ```
   pip install -r requirements.txt
   ```

- For the text-processing part, we use `spaCy`. You need to download the English model by running the following command:

   ```
    python -m spacy download en_core_web_sm
   ```

5. **Start developing the project**
