# invoice-processor-documentai

# Invoice Extraction & Processing with Google Document AI

## Overview
This project automates the extraction of invoice data using Google Cloud's Document AI API and stores it in a MySQL database. It processes invoices in various formats such as PDF, PNG, JPG, and WEBP to extract fields like invoice ID, total amount, due date, and line items. The extracted information is then stored in a structured format for easy retrieval.

## Features
- Supports document formats: PDF, PNG, JPG, JPEG, WEBP
- Extracts entities such as invoice date, total amount, and line items
- Saves extracted data to a MySQL database
- Dynamic creation of database tables for invoice and item information

## Prerequisites
- Python 3.x
- MySQL server
- Google Cloud Account with Document AI enabled
- Google Cloud credentials file (JSON)
- Installed Python packages: `pymysql`, `google-cloud-documentai`

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/invoice-processor-documentai.git
    cd invoice-processor-documentai
    ```

2. Install the required dependencies:
    ```bash
    pip install pymysql google-cloud-documentai
    ```

3. Set up your MySQL database and configure the `DB_HOST`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME` in the code.

4. Set up Google Cloud:
    - Enable the Document AI API in your Google Cloud project.
    - Download the service account key file (JSON) and update the path in the script:  
      `SERVICE_ACCOUNT_FILE = "/path/to/your/service_account.json"`

5. Set the Google credentials environment variable:
    ```bash
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service_account.json"
    ```

## Usage

1. Add your document (e.g., PDF, PNG, JPG) to the `DOCUMENT_PATH` variable in the script.
   
2. Run the script:
    ```bash
    python main.py
    ```

3. The extracted data will be saved as a JSON file (`output_data.json`), and the invoice details will be stored in the MySQL database.

## Database Schema
- **invoice_info**: Contains general information about each invoice (e.g., invoice ID, date, total amount).
- **item**: Contains details of individual items in the invoice (e.g., description, quantity, unit price).

## Google Cloud Document AI
This project uses Google Cloud's Document AI to parse the invoice and identify key fields like invoice date, total amount, and item details. 

For more information, see the [Google Cloud Document AI Documentation](https://cloud.google.com/document-ai/docs).

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contributing
Feel free to open issues or submit pull requests to contribute to this project.

