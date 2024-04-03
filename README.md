# Azure Function for Automated SEO optimized Image Description and Management

## Overview

This Azure Function automates the process of handling image uploads to a specified Blob storage container. Upon the upload of an image file, the function evaluates the file's extension. If the extension is allowed, the function generates a descriptive alt-text for the image using Azure's AI capabilities and inserts this description into a CosmosDB database. If the file extension is not allowed, the file is automatically deleted from the Blob storage.

## Key Features

- **Automated File Handling**: Automatically processes uploaded images based on file extension.
- **AI-Generated Descriptions**: Utilizes Azure OpenAI to generate SEO-compliant descriptive alt-texts for images.
- **Database Integration**: Inserts the generated descriptions into CosmosDB for easy retrieval and management.
- **Security and Access Management**: Generates a temporary SAS URL for the image, ensuring secure access for description generation without exposing sensitive data.

## Requirements

- Azure Subscription
- Azure Storage Account with Blob service
- Azure CosmosDB account
- Azure OpenAI resource

## Configuration

1. **Environment Variables**: Set the following environment variables in your function app configuration:
   - `images06_STORAGE`: Connection string for the Azure Storage account.
   - `ACCOUNT_URI`: The URI for the CosmosDB account.
   - `ACCOUNT_KEY`: The key for the CosmosDB account.
   - `AZURE_OPENAI_ENDPOINT`: The endpoint URL for the Azure OpenAI service.
   - `AZURE_OPENAI_API_KEY`: The API key for accessing Azure OpenAI.
   - `key_storage_account`: The key for the Blob storage account, used in generating SAS URLs.

2. **CosmosDB Setup**:
   - Database Name: `descriptions`
   - Container Name: `products_descriptions`

3. **Supported File Extensions**:
   - `.png`, `.jpeg`, `.jpg`, `.tiff`, `.gif`, `.bmp`, `.webp`

## How It Works

1. **Trigger**: The function is triggered by the upload of a file to the Blob storage container.
2. **File Validation**: Validates the file extension. If not allowed, the file is deleted.
3. **Description Generation**: For allowed files, generates a descriptive alt-text using Azure OpenAI.
4. **Database Insertion**: Inserts the generated description into CosmosDB.

## Security

- Temporary SAS URLs ensure that the images are accessed securely by the function for description generation.
- Sensitive information such as database keys and storage account details are stored in environment variables, not hardcoded.

## Deployment

Deploy this function through the Azure Portal, Azure CLI, or your preferred CI/CD pipeline, ensuring that all required resources are created and configured before deployment.

## Logging

The function includes logging for key actions and errors, aiding in monitoring and troubleshooting.

---

**Note**: This function requires appropriate configuration of Azure resources and permissions. Ensure that your Azure OpenAI resource is configured to handle image-based requests and that your CosmosDB and Blob storage are correctly set up and accessible to the function.
