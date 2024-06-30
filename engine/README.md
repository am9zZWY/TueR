# Search Engine

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

   - Create a directory for your project:

    ```
    mkdir ~/.venvs/
    cd ~/.venvs/
    ```

   - Create the virtual environment:

    ```
    virtualenv --python=3.11 3.11
    ```

   - Activate the virtual environment:

    ```
    source ~/.venvs/3.11/bin/activate
    ```

4. **Install requirements:**

   - Ensure you have a requirements.txt file in your project directory.
   - Run the following command to install the dependencies:

   ```
   pip install -r requirements.txt
   ```

5. **Start developing the project**
