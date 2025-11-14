# PublicBridge AI Demo Guide

## Quick Start Demo

This guide will walk you through the key AI features of PublicBridge. Follow these steps to see the AI integration in action.

## 1. AI Dashboard Demo

### Access the AI Dashboard
1. Navigate to: `http://127.0.0.1:8000/dashboard/ai/`
2. You should see the AI Dashboard with:
   - Real-time AI processing statistics
   - Report sentiment analysis charts
   - Hotspot detection maps
   - User behavior insights

### What to Look For
- **Processing Status**: Shows how many reports have been AI-processed
- **Confidence Scores**: Displays AI confidence levels for different analyses
- **Trend Analysis**: Shows patterns in report submissions over time
- **Hotspot Map**: Visual representation of high-activity areas

## 2. AI Chatbot Demo

### Access the Chatbot
1. Navigate to: `http://127.0.0.1:8000/dashboard/ai/chatbot/`
2. Try these example queries:

```
"What are the most common issues reported this week?"
"Show me reports about infrastructure problems"
"What's the sentiment of recent reports?"
"Are there any emerging issues I should know about?"
```

### Expected Responses
- **Data Analysis**: The chatbot should provide statistics and insights
- **Trend Identification**: It should identify patterns in the data
- **Sentiment Analysis**: It should summarize the emotional tone of reports
- **Recommendations**: It should suggest actions based on the data

## 3. Report Analysis Demo

### Submit a Test Report
1. Go to: `http://127.0.0.1:8000/reports/submit/`
2. Create a report with this content:
   - **Title**: "Pothole causing traffic delays"
   - **Description**: "Large pothole on Main Street near the intersection with Oak Avenue. Multiple cars have been damaged. This is a safety hazard that needs immediate attention."
   - **Category**: "Infrastructure"
   - **Priority**: "High"

### View AI Analysis
1. After submission, navigate to your reports list
2. Click on the report you just created
3. Look for the AI Insights section which should show:
   - **Sentiment**: Likely "Negative" due to safety concerns
   - **Keywords**: "pothole", "traffic", "safety", "hazard"
   - **Predicted Priority**: "High" (based on safety keywords)
   - **Confidence Score**: Should be above 0.8 for clear content

## 4. API Demo

### Test AI API Endpoints

#### Get AI-Enhanced Reports
```bash
curl http://127.0.0.1:8000/reports/api/ai/reports/
```

Expected response should include reports with AI insights like:
```json
{
  "count": 25,
  "results": [
    {
      "id": 1,
      "title": "Pothole on Main Street",
      "ai_confidence_score": 0.85,
      "ai_predicted_priority": "high",
      "ai_hotspot_prediction": true,
      "ai_insights": {
        "confidence_score": 0.85,
        "recommendations": ["Immediate attention required"],
        "predicted_priority": "high"
      }
    }
  ]
}
```

#### Process Reports with AI
```bash
curl -X POST http://127.0.0.1:8000/reports/api/ai/reports/process/ \
  -H "Content-Type: application/json" \
  -d '{
    "processing_type": "report_analysis",
    "target_ids": [1, 2, 3]
  }'
```

#### Get AI Dashboard Stats
```bash
curl http://127.0.0.1:8000/reports/api/ai/dashboard/stats/
```

Expected response:
```json
{
  "reports": {
    "total": 100,
    "ai_processed": 75,
    "ai_processed_percentage": 75.0,
    "hotspot_predictions": 15,
    "high_confidence": 60
  },
  "users": {
    "total": 50,
    "ai_analyzed": 30,
    "ai_analyzed_percentage": 60.0,
    "high_risk": 2
  }
}
```

## 5. User Behavior Analysis Demo

### Create Test Users
1. Register a few test users with different behaviors
2. Have each user submit reports with different characteristics:
   - User 1: Submit 5 reports about different topics
   - User 2: Submit 3 reports about the same issue repeatedly
   - User 3: Submit 1 report with very detailed descriptions

### View AI User Analysis
1. Access the user management section
2. Look for users with AI insights
3. Check for:
   - **Behavior Scores**: Range from 0.0 to 1.0
   - **Risk Levels**: Low, Medium, High
   - **Activity Patterns**: Frequency and types of reports

## 6. Hotspot Detection Demo

### Create Geographic Cluster
1. Submit multiple reports from the same geographic area:
   - Use similar coordinates for 5-10 reports
   - Use related categories (e.g., all infrastructure issues)
   - Submit over a short time period

### View Hotspot Map
1. Navigate to the AI Dashboard
2. Look for the Hotspot Detection section
3. The area should be highlighted as a hotspot
4. Check the confidence level of the hotspot prediction

## 7. Trend Analysis Demo

### Create Temporal Pattern
1. Submit reports following a pattern:
   - Week 1: 5 infrastructure reports
   - Week 2: 8 infrastructure reports
   - Week 3: 12 infrastructure reports
   - Week 4: 15 infrastructure reports

### View Trend Analysis
1. Access the AI Dashboard trends section
2. Look for the infrastructure category trend
3. The system should identify the upward trend
4. Check for trend confidence and predictions

## 8. Batch Processing Demo

### Process Multiple Reports
1. Use the API to process multiple reports at once:

```bash
curl -X POST http://127.0.0.1:8000/reports/api/ai/reports/process/ \
  -H "Content-Type: application/json" \
  -d '{
    "processing_type": "batch_analysis",
    "custom_parameters": {
      "confidence_threshold": 0.8,
      "max_batch_size": 50
    }
  }'
```

### Monitor Processing
1. Check the processing status in the AI Dashboard
2. Look for batch processing statistics
3. Verify that reports have been updated with AI insights

## 9. Error Handling Demo

### Test Error Scenarios
1. Try to process a non-existent report:
```bash
curl -X POST http://127.0.0.1:8000/reports/api/ai/reports/process/ \
  -d '{"target_ids": [99999]}'
```

2. Try to access AI data without proper permissions

### Expected Behavior
- Graceful error messages
- Proper HTTP status codes
- No system crashes
- Appropriate logging

## 10. Performance Demo

### Load Test
1. Create 50+ test reports quickly
2. Process them all with AI
3. Monitor:
   - Response times
   - Memory usage
   - Processing queue length
   - Success/failure rates

### Expected Performance
- Individual report processing: < 2 seconds
- Batch processing: < 30 seconds for 50 reports
- API response times: < 500ms for simple queries
- Memory usage: Stable, no memory leaks

## Troubleshooting Demo Issues

### Common Issues and Solutions

1. **AI Dashboard Not Loading**
   - Check if AI agents are properly initialized
   - Verify database connections
   - Check for JavaScript errors in browser console

2. **No AI Insights Showing**
   - Ensure reports have been processed with AI
   - Check if AI processing is enabled in settings
   - Verify that AI models are loaded correctly

3. **API Errors**
   - Check URL patterns and routing
   - Verify authentication/permissions
   - Check request format and parameters

4. **Chatbot Not Responding**
   - Check if chatbot agent is initialized
   - Verify natural language processing models
   - Check for backend errors in logs

5. **Slow Performance**
   - Check system resources (CPU, memory)
   - Verify database optimization
   - Consider enabling caching

## Demo Data Setup

### Quick Setup Script
If you need to quickly populate demo data, you can use the management commands:

```bash
# Create demo reports with AI analysis
python manage.py create_demo_reports --count=50 --with-ai

# Create demo users with varied behaviors
python manage.py create_demo_users --count=10 --with-activity

# Process all existing reports with AI
python manage.py process_reports_with_ai --all
```

### Manual Data Creation
For more controlled testing, manually create:
- 10-20 reports with varied content
- 3-5 test users
- Reports in different categories
- Reports from different time periods
- Reports with different sentiment levels

## Next Steps After Demo

1. **Customization**: Modify AI models for your specific use case
2. **Training**: Train AI models with your local data
3. **Integration**: Integrate with external systems
4. **Monitoring**: Set up monitoring and alerting
5. **Scaling**: Plan for production deployment

## Support

If you encounter issues during the demo:
- Check the troubleshooting section above
- Review the main AI documentation
- Check system logs for error messages
- Ensure all dependencies are properly installed

---

*This demo guide is updated regularly. Last updated: January 2024*