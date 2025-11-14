# AI Authentication and Model Access Guide

## Overview
This guide explains how to set up authentication for AI models and provides alternatives for publicly available models.

## Current Status
The system is configured to use publicly available models by default, but you can optionally set up authentication for premium models.

## Authentication Options

### Option 1: Use Public Models (Default - No Authentication Required)
The system is already configured to use these public models:

- **Chatbot**: `microsoft/DialoGPT-medium` (conversational AI)
- **Sentiment Analysis**: `distilbert-base-uncased-finetuned-sst-2-english`
- **Emotion Detection**: `j-hartmann/emotion-english-distilroberta-base`
- **Text Classification**: `distilbert-base-uncased` with custom classification head

### Option 2: Set Up Hugging Face Authentication (Optional)
If you want to use premium models like Llama 3.1:

1. **Create a Hugging Face account** at https://huggingface.co/join
2. **Request access to Llama models**:
   - Go to https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct
   - Click "Request Access" and fill out the form
   - Wait for approval (usually 1-2 business days)
3. **Create an access token**:
   - Go to https://huggingface.co/settings/tokens
   - Click "New token"
   - Give it a name like "PublicBridgeAI"
   - Select "Read" permissions
   - Copy the token
4. **Set up authentication**:
   ```bash
   # Set environment variable (temporary)
   export HUGGINGFACE_TOKEN="your_token_here"
   
   # Or create a .env file in your project root
   echo "HUGGINGFACE_TOKEN=your_token_here" > .env
   ```

### Option 3: Use Environment Variables (Recommended)
Create a `.env` file in your project root:

```bash
# Optional: Hugging Face token for premium models
HUGGINGFACE_TOKEN=your_token_here

# Optional: Use specific models
CHATBOT_MODEL=microsoft/DialoGPT-medium
SENTIMENT_MODEL=distilbert-base-uncased-finetuned-sst-2-english
CLASSIFIER_MODEL=distilbert-base-uncased
```

## Updated Model Configuration

The AI agents have been updated to use these public models by default:

### CivicChatbotAgent
```python
# Default: microsoft/DialoGPT-medium (public)
# Fallback: microsoft/DialoGPT-small (public)
# Optional: meta-llama/Llama-3.1-8B-Instruct (requires auth)
```

### AdvancedSentimentAnalyzer
```python
# Sentiment: distilbert-base-uncased-finetuned-sst-2-english (public)
# Emotion: j-hartmann/emotion-english-distilroberta-base (public)
# Language Detection: papluca/xlm-roberta-base-language-detection (public)
```

### LlamaClassifierAgent
```python
# Default: microsoft/DialoGPT-medium (public)
# Fallback: distilbert-base-uncased (public)
# Optional: meta-llama/Llama-3.1-8B-Instruct (requires auth)
```

## Testing Your Setup

### Test 1: Basic Functionality (No Auth Required)
```bash
python test_basic_ai.py
```

### Test 2: Full Integration Test (Optional)
```bash
# If you have set up authentication
python test_ai_agents.py
```

## Troubleshooting

### Model Download Issues
If models are downloading slowly or failing:
1. Check your internet connection
2. Try using smaller models (DialoGPT-small instead of medium)
3. Use the fallback mechanisms built into the system

### Memory Issues
If you run out of memory:
1. Use smaller models (DialoGPT-small, distilbert-base-uncased)
2. Reduce batch sizes in the code
3. Use CPU instead of GPU for testing

### Authentication Issues
If authentication fails:
1. Verify your token is correct
2. Check if you have access to the specific model
3. Use public models as fallback

## Performance Comparison

| Model | Size | Speed | Quality | Auth Required |
|-------|------|-------|---------|---------------|
| DialoGPT-small | 120M | Fast | Good | No |
| DialoGPT-medium | 350M | Medium | Better | No |
| Llama 3.1 8B | 8B | Slow | Best | Yes |
| DistilBERT | 66M | Fast | Good | No |

## Recommendations

1. **For Development**: Use public models (DialoGPT-medium, DistilBERT)
2. **For Production**: Set up authentication for Llama models if you need the best quality
3. **For Testing**: Use the basic test script to verify functionality

## Next Steps

The system is now configured to work out-of-the-box with public models. You can:

1. Run the basic tests to verify everything works
2. Set up authentication later if you need premium features
3. Deploy to production with the public models
4. Monitor performance and upgrade models as needed