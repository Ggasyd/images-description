import logging
import os
from datetime import datetime, timedelta
import azure.functions as func
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.core.exceptions import ResourceNotFoundError
from azure.cosmos import CosmosClient, exceptions
from azure.cosmos.exceptions import CosmosResourceExistsError
from openai import AzureOpenAI

allowed_extensions = ['.png', '.jpeg', '.jpg', '.tiff', '.gif', '.bmp', '.webp']

def main(myblob: func.InputStream):
    
    """
    Cette fonction est déclenchée lorsqu'un blob est téléchargé dans le conteneur spécifié.
    Si l'extension du fichier est autorisée, génère une description et l'insère dans CosmosDB.
    SI l'extension du fichier n'est pas autorisée, le fichier est automatiquement supprimé.
    """
    logging.info(f"Processed blob\nName: {myblob.name}\nSize: {myblob.length} bytes")

    file_name = os.path.basename(myblob.name)
    file_extension = os.path.splitext(file_name)[1].lower()
    container_name = "images-description"
    connect_str = os.getenv('images06_STORAGE')

    URL = os.environ['ACCOUNT_URI']
    KEY = os.environ['ACCOUNT_KEY']
    client = CosmosClient(URL, credential=KEY)
    DATABASE_NAME = 'descriptions'
    CONTAINER_NAME = 'products_descriptions'
    database = client.get_database_client(DATABASE_NAME)
    container = database.get_container_client(CONTAINER_NAME)
    
    full_path = myblob.name
    extracted_path = '/'.join(full_path.split('/')[1:])
    
    if file_extension in allowed_extensions:

        if not check_description_exists(file_name, container):

            sas_url = generate_blob_sas_url(container_name, connect_str, full_path)
            description = generate_image_description(sas_url)
            insert_into_cosmosdb([description], container)

        else:

            logging.info(f"Description already exists for blob {file_name}. No action taken.")

    else:

        try:

            blob_service_client = BlobServiceClient.from_connection_string(connect_str)
            blob_container_client = blob_service_client.get_container_client(container_name)
            blob_client = blob_container_client.get_blob_client(extracted_path)
            blob_client.delete_blob()
            logging.info(f"Blob {extracted_path} deleted successfully as it is not an allowed file type.")

        except ResourceNotFoundError:

            logging.info(f"Blob {extracted_path} does not exist. No deletion needed.")

        except Exception as e:

            logging.error(f"Could not delete blob: {extracted_path}. Error: {e}")



def generate_blob_sas_url(container_name: str, connection_string: str, blob_path: str):

    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    account_key = os.getenv('key_storage_account')
    blob_name = '/'.join(blob_path.split('/')[1:])
    sas_token = generate_blob_sas(account_name=blob_service_client.account_name,
                                  account_key=account_key,
                                  container_name=container_name,
                                  blob_name=blob_name,
                                  permission=BlobSasPermissions(read=True),
                                  expiry=datetime.utcnow() + timedelta(hours=1))
    return f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"




def generate_image_description(blob_url_with_sas: str) -> dict:

    api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = '2024-02-15-preview'

    client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=api_base
    )

    response = client.chat.completions.create(
        model="image-bot",
        messages=[
            {"role": "system", "content": "You are a french SEO expert, with many years of experience."},
            {"role": "user", "content": [
                {"type": "text", "text": "Generate an SEO compliant sentence for product image alt-text in french. Focus on the product, not the background objects."},
                {"type": "image_url", "image_url": {"url": blob_url_with_sas}}
            ]}
        ],
        max_tokens=300
    )

    description = response.choices[0].message.content

    return {"url": blob_url_with_sas.split('?')[0], "description": description}




def insert_into_cosmosdb(alt_texts: list, container):
    for alt_text in alt_texts:
        try:
            item = {'id': alt_text['url'].split('/')[-1], 'url': alt_text['url'], 'description': alt_text['description']}
            container.create_item(body=item)
        except CosmosResourceExistsError as e:
            logging.warning(f"Item with id {item['id']} already exists in Cosmos DB. No new item created. Error: {e}")
        except exceptions.CosmosHttpResponseError as e:
            logging.error(f"Could not insert item into Cosmos DB. Error: {e}")




def check_description_exists(blob_name: str, container) -> bool:
    try:
        item = container.read_item(item=blob_name, partition_key=blob_name)
        logging.info(f"Description for blob {blob_name} already exists in Cosmos DB.")
        return True
    except exceptions.CosmosResourceNotFoundError:
        return False
