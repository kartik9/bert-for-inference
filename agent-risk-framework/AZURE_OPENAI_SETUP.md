# Azure OpenAI Setup Guide

Complete guide for using the AI Agent Risk Assessment Framework with Azure OpenAI instead of standard OpenAI.

## Why Use Azure OpenAI?

- **Enterprise compliance**: Azure OpenAI meets enterprise compliance requirements
- **Data privacy**: Your data stays in your Azure region
- **Cost control**: Better cost management through Azure subscriptions
- **Integration**: Seamless integration with other Azure services

## Prerequisites

1. **Azure Subscription** with Azure OpenAI access
2. **Azure OpenAI Resource** deployed
3. **GPT Model Deployment** (e.g., gpt-4, gpt-35-turbo)

## Step 1: Get Your Azure OpenAI Credentials

### Find Your Endpoint

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your Azure OpenAI resource
3. Click on **Keys and Endpoint** in the left menu
4. Copy the **Endpoint** (e.g., `https://your-resource.openai.azure.com/`)

### Get Your API Key

From the same **Keys and Endpoint** page:
- Copy either **KEY 1** or **KEY 2**

### Find Your Deployment Name

1. In your Azure OpenAI resource, click **Model deployments**
2. Click **Manage Deployments** or go to Azure OpenAI Studio
3. Note your deployment name (e.g., `gpt-4`, `gpt-35-turbo`, `my-gpt-deployment`)

## Step 2: Configure the Framework

### Option A: Using .env File (Recommended)

Edit your `.env` file:

```bash
# Set to true to use Azure OpenAI
USE_AZURE_OPENAI=true

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_actual_azure_key_here
AZURE_OPENAI_DEPLOYMENT=gpt-4

# Optional: API version (default is 2024-02-15-preview)
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Standard OpenAI key not needed when using Azure
# OPENAI_API_KEY=not_needed
```

### Option B: Environment Variables

```bash
export USE_AZURE_OPENAI=true
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your_actual_azure_key_here"
export AZURE_OPENAI_DEPLOYMENT="gpt-4"
```

## Step 3: Test Your Configuration

### Quick Test

```bash
# Start the server
./run_server.sh

# In another terminal, test with any GPT
./venv/bin/python test_real_gpt.py g-h8l4uLHFQ
```

### Verify Configuration

```bash
./venv/bin/python -c "
from src.config import settings
print('Azure OpenAI Configuration:')
print(f'  Enabled: {settings.use_azure_openai}')
print(f'  Endpoint: {settings.azure_openai_endpoint}')
print(f'  Deployment: {settings.azure_openai_deployment}')
print(f'  API Version: {settings.azure_openai_api_version}')
"
```

## Step 4: Run Assessments

Once configured, use the framework exactly as before:

```bash
# Test a GPT from the store
./venv/bin/python test_real_gpt.py "https://chatgpt.com/g/g-h8l4uLHFQ-video-ai-by-invideo"

# Or use the API
curl -X POST http://localhost:8000/api/v1/assessments \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "openai_gpt",
    "agent_identifier": "g-h8l4uLHFQ",
    "assessment_level": "standard"
  }'
```

No code changes needed! The framework automatically uses Azure OpenAI when configured.

## Configuration Reference

### Required Settings

| Setting | Description | Example |
|---------|-------------|---------|
| `USE_AZURE_OPENAI` | Enable Azure OpenAI | `true` |
| `AZURE_OPENAI_ENDPOINT` | Your Azure OpenAI endpoint | `https://myresource.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | Your Azure OpenAI API key | `abc123...xyz` |
| `AZURE_OPENAI_DEPLOYMENT` | Your deployment name | `gpt-4` or `my-gpt-deployment` |

### Optional Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `AZURE_OPENAI_API_VERSION` | Azure API version | `2024-02-15-preview` |

## Switching Between Standard and Azure OpenAI

You can easily switch between standard OpenAI and Azure OpenAI:

### Use Azure OpenAI
```bash
# .env
USE_AZURE_OPENAI=true
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_azure_key
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

### Use Standard OpenAI
```bash
# .env
USE_AZURE_OPENAI=false
OPENAI_API_KEY=sk-proj-your-standard-openai-key
```

Just change `USE_AZURE_OPENAI` and restart the server!

## Supported Azure OpenAI Models

The framework works with any Azure OpenAI deployment:

- **GPT-4 Models**: `gpt-4`, `gpt-4-32k`, `gpt-4-turbo`
- **GPT-3.5 Models**: `gpt-35-turbo`, `gpt-35-turbo-16k`
- **Custom Deployments**: Any name you gave your deployment

**Note**: Make sure your deployment has sufficient quota for testing (the framework sends ~10 test messages per assessment).

## API Versions

Azure OpenAI API versions you can use:

- `2024-02-15-preview` (recommended, default)
- `2023-12-01-preview`
- `2023-05-15`

See [Azure OpenAI API Versions](https://learn.microsoft.com/en-us/azure/ai-services/openai/reference) for the latest.

## Troubleshooting

### Error: "AZURE_OPENAI_ENDPOINT must be set"

**Solution**: Add your Azure endpoint to `.env`:
```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
```

### Error: "AZURE_OPENAI_DEPLOYMENT must be set"

**Solution**: Add your deployment name to `.env`:
```bash
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

### Error: "Error communicating with Azure OpenAI: 404"

**Causes**:
1. Deployment name is incorrect
2. API version is not supported
3. Endpoint URL is wrong

**Solution**: Double-check your deployment name in Azure OpenAI Studio and verify the endpoint URL.

### Error: "Error communicating with Azure OpenAI: 401"

**Cause**: Invalid API key

**Solution**:
1. Verify your API key in Azure Portal (Keys and Endpoint)
2. Make sure you copied the entire key
3. Try regenerating the key if needed

### Error: "Error communicating with Azure OpenAI: 429"

**Cause**: Rate limit or quota exceeded

**Solution**:
1. Check your deployment quota in Azure OpenAI Studio
2. Increase tokens-per-minute (TPM) quota if needed
3. Wait a moment and try again

### Endpoint Format Issues

**Correct formats**:
```bash
✅ https://your-resource.openai.azure.com/
✅ https://your-resource.openai.azure.com
```

**Incorrect formats**:
```bash
❌ your-resource.openai.azure.com (missing https://)
❌ https://your-resource.openai.azure.com/openai (extra path)
```

## Cost Considerations

Azure OpenAI pricing is based on:
- **Token usage**: Input + output tokens
- **Deployment type**: Standard vs. Provisioned Throughput

**Typical assessment costs**:
- Standard assessment: ~10 test messages
- Average per assessment: ~10,000 tokens
- Cost per assessment: ~$0.30 for GPT-4, ~$0.02 for GPT-3.5

See [Azure OpenAI Pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/) for current rates.

## Security Best Practices

1. **Use Key Vault**: Store your API key in Azure Key Vault instead of .env files
2. **Rotate Keys**: Regularly rotate your API keys
3. **Network Security**: Use Azure Private Link for added security
4. **Monitor Usage**: Set up alerts for unusual usage patterns
5. **Managed Identity**: Use Azure Managed Identity when deploying to Azure

## Example: Complete .env for Azure

```bash
# Application Settings
ENV=production
LOG_LEVEL=INFO

# Azure OpenAI (Primary)
USE_AZURE_OPENAI=true
AZURE_OPENAI_ENDPOINT=https://mycompany-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=1234567890abcdef1234567890abcdef
AZURE_OPENAI_DEPLOYMENT=gpt-4-deployment
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Standard OpenAI (Fallback - optional)
# OPENAI_API_KEY=sk-proj-fallback-key

# Database
DATABASE_URL=sqlite:///./agent_assessments.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

## Getting Help

If you encounter issues:

1. Check [Azure OpenAI Service Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
2. Verify your deployment in [Azure OpenAI Studio](https://oai.azure.com/)
3. Review Azure OpenAI [troubleshooting guide](https://learn.microsoft.com/en-us/azure/ai-services/openai/troubleshooting)
4. Open an issue on our GitHub repository

## Next Steps

Once configured:
1. Test with featured GPTs: `./venv/bin/python test_real_gpt.py --featured`
2. Run your first assessment
3. View nutrition labels in your browser
4. Integrate into your CI/CD pipeline

Happy testing with Azure OpenAI! 🚀
