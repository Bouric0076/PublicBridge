# Groq Models Configuration (November 2025)

## Current Supported Models

### Production Models
| Model Name | Description | Context Length | Use Case |
|------------|-------------|----------------|----------|
| `llama-3.1-8b-instant` | Fast, smaller LLaMA 3.1 variant | 8k | Quick responses, simple queries |
| `llama-3.1-70b-versatile` | Large, reasoning-capable LLaMA 3.1 | 8k | Complex reasoning, detailed analysis |
| `gemma2-9b-it` | Good mid-range chat model | 8k | Balanced performance |
| `llama-3.2-90b-vision-preview` | Multimodal (text + image) | 8k | Image analysis (future feature) |

### Deprecated Models (DO NOT USE)
- ❌ `mixtral-8x7b-32768` - **DECOMMISSIONED**
- ❌ `mixtral-8x22b` - **DEPRECATED**

## PublicBridge Implementation

### Model Selection Strategy
1. **Fast Model** (`llama-3.1-8b-instant`): 
   - Input length < 50 characters
   - Simple queries, quick responses
   - Classification tasks

2. **Balanced Model** (`gemma2-9b-it`):
   - Input length 50-200 characters
   - Medium complexity queries
   - General conversation

3. **Powerful Model** (`llama-3.1-70b-versatile`):
   - Input length > 200 characters
   - Complex reasoning required
   - Detailed analysis

### Configuration Files Updated
- `ai_agents/groq_chatbot.py` - Dynamic model selection
- `ai_agents/groq_classifier.py` - Fast model for classification
- Both files include fallback mechanisms

### API Key Configuration
Set in `.env` file:
```
GROQ_API_KEY=your-groq-api-key-here
```

### Error Handling
- Automatic fallback to rule-based responses if Groq API fails
- Model selection failure defaults to fast model
- Comprehensive logging for debugging

## Testing
After updating models, test with:
```bash
python manage.py runserver
```

Check logs for:
- ✅ No "model_decommissioned" errors
- ✅ Successful API calls
- ✅ Proper model selection logging

## Future Considerations
- Monitor Groq's deprecation notices: https://console.groq.com/docs/deprecations
- Consider `llama-3.2-90b-vision-preview` for image analysis features
- Update model selection logic based on performance metrics
