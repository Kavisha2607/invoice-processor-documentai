import os
import pymysql
import json
from google.api_core.client_options import ClientOptions
from google.cloud import documentai_v1 as documentai
from typing import Dict, Any

# Constants
PROJECT_ID = ""  # Add your project ID here
LOCATION = ""  # Add the location here
PROCESSOR_ID = ""  # Add your processor ID here
DOCUMENT_PATH = ""  # Add the path to your document file here
SERVICE_ACCOUNT_FILE = ""  # Add the path to your service account file here

# MySQL Database Config
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = ''  # Update to your actual password
DB_NAME = 'invoice'

# Set the GOOGLE_APPLICATION_CREDENTIALS environment variable
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE

def process_document_sample(
    project_id: str,
    location: str,
    processor_id: str,
    image_content,
    mime_type: str,
) -> documentai.Document:
    opts = ClientOptions(api_endpoint=f"{location}-documentai.googleapis.com")
    client = documentai.DocumentProcessorServiceClient(client_options=opts)
    name = client.processor_path(project_id, location, processor_id)
    raw_document = documentai.RawDocument(content=image_content, mime_type=mime_type)
    request = documentai.ProcessRequest(name=name, raw_document=raw_document)
    result = client.process_document(request=request)
    return result.document

def extract_entities_and_form_fields(document) -> Dict[str, Any]:
    data = {"entities": [], "form_fields": {}}
    
    # Extract entities
    for ent in document.entities:
        entity_info = {
            "type": ent.type_,
            "mention_text": ent.mention_text,
            "properties": [
                {"type": prop.type_, "mention_text": prop.mention_text}
                for prop in ent.properties
            ]
        }
        data["entities"].append(entity_info)
    
    # Extract form fields
    for page in document.pages:
        for field in page.form_fields:
            field_name = get_text(field.field_name, document).strip()
            field_value = get_text(field.field_value, document).strip()
            
            if field_name:
                data["form_fields"][field_name] = field_value
    
    return data

def get_text(doc_element, document) -> str:
    response = ""
    if not doc_element or not doc_element.text_anchor:
        return response

    for segment in doc_element.text_anchor.text_segments:
        start_index = int(segment.start_index) if segment.start_index else 0
        end_index = int(segment.end_index)
        response += document.text[start_index:end_index]
    
    return response

def save_output_to_json(data: Dict[str, Any], json_file_path: str):
    with open(json_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    print(f"Output saved to {json_file_path}")

def create_tables():
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()

        # Create invoice_info table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoice_info (
                inv_id INT AUTO_INCREMENT PRIMARY KEY,
                invoice_date TEXT,
                invoice_id TEXT,
                due_date TEXT,
                total_amount TEXT,
                net_amount TEXT,
                total_tax_amount TEXT,
                supplier_email TEXT,
                supplier_address TEXT,
                currency TEXT,
                supplier_name TEXT,
                receiver_name TEXT,
                remit_to_address TEXT
            )
        """)

        # Create item table with a foreign key to invoice_info
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS item (
                id INT AUTO_INCREMENT PRIMARY KEY,
                invoice_id INT,
                description TEXT,
                quantity TEXT,
                unit_price TEXT,
                total TEXT,
                FOREIGN KEY (invoice_id) REFERENCES invoice_info(inv_id)
            )
        """)

        conn.commit()
        print("Tables created successfully.")
    except pymysql.MySQLError as e:
        print(f"Database error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def store_entities_and_fields(form_fields: Dict[str, Any], entities: Dict[str, Any]):
    conn = None
    cursor = None
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()

        # Extract the fields
        invoice_date = next((ent['mention_text'] for ent in entities['entities'] if ent['type'] == 'invoice_date'), '')
        invoice_id = next((ent['mention_text'] for ent in entities['entities'] if ent['type'] == 'invoice_id'), '')
        due_date = next((ent['mention_text'] for ent in entities['entities'] if ent['type'] == 'due_date'), '')
        total_amount = next((ent['mention_text'] for ent in entities['entities'] if ent['type'] == 'total_amount'), '')
        net_amount = next((ent['mention_text'] for ent in entities['entities'] if ent['type'] == 'net_amount'), '')
        total_tax_amount = next((ent['mention_text'] for ent in entities['entities'] if ent['type'] == 'total_tax_amount'), '')
        supplier_email = next((ent['mention_text'] for ent in entities['entities'] if ent['type'] == 'supplier_email'), '')
        supplier_address = next((ent['mention_text'] for ent in entities['entities'] if ent['type'] == 'supplier_address'), '')
        currency = next((ent['mention_text'] for ent in entities['entities'] if ent['type'] == 'currency'), '')
        supplier_name = next((ent['mention_text'] for ent in entities['entities'] if ent['type'] == 'supplier_name'), '')
        receiver_name = next((ent['mention_text'] for ent in entities['entities'] if ent['type'] == 'receiver_name'), '')
        remit_to_address = next((ent['mention_text'] for ent in entities['entities'] if ent['type'] == 'remit_to_address'), '')

        # Insert invoice_info
        cursor.execute("""
            INSERT INTO invoice_info (
                invoice_date, invoice_id, due_date, total_amount, net_amount, 
                total_tax_amount, supplier_email, supplier_address, currency, 
                supplier_name, receiver_name, remit_to_address
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            invoice_date,
            invoice_id,
            due_date,
            total_amount,
            net_amount,
            total_tax_amount,
            supplier_email,
            supplier_address,
            currency,
            supplier_name,
            receiver_name,
            remit_to_address
        ))

        invoice_id = cursor.lastrowid
        print(f"Inserted invoice_info with ID: {invoice_id}")

        # Insert line items
        for item in [ent for ent in entities['entities'] if ent['type'] == 'line_item']:
            description = next((prop['mention_text'] for prop in item['properties'] if prop['type'] == 'line_item/description'), '')
            quantity = next((prop['mention_text'] for prop in item['properties'] if prop['type'] == 'line_item/quantity'), '')
            unit_price = next((prop['mention_text'] for prop in item['properties'] if prop['type'] == 'line_item/unit_price'), '')
            total = next((prop['mention_text'] for prop in item['properties'] if prop['type'] == 'line_item/amount'), '')

            cursor.execute("""
                INSERT INTO item (
                    invoice_id, description, quantity, unit_price, total
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                invoice_id,
                description,
                quantity,
                unit_price,
                total
            ))

        conn.commit()
        print("Invoice and line items inserted successfully.")
    except pymysql.MySQLError as e:
        print(f"Database error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    create_tables()  # Ensure tables exist before inserting data

    if DOCUMENT_PATH.lower().endswith('.pdf'):
        mime_type = 'application/pdf'
    elif DOCUMENT_PATH.lower().endswith('.png'):
        mime_type = 'image/png'
    elif DOCUMENT_PATH.lower().endswith('.webp'):
        mime_type = 'image/webp'
    elif DOCUMENT_PATH.lower().endswith('.jpg') or DOCUMENT_PATH.lower().endswith('.jpeg'):
        mime_type = 'image/jpeg'
    else:
        raise ValueError("Unsupported file type.")

    with open(DOCUMENT_PATH, "rb") as file:
        image_content = file.read()

    try:
        document = process_document_sample(
            PROJECT_ID, LOCATION, PROCESSOR_ID, image_content, mime_type
        )
        data = extract_entities_and_form_fields(document)
        save_output_to_json(data, 'output_data.json')
        store_entities_and_fields(data['form_fields'], data)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
