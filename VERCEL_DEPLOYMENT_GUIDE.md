# Vercel Deployment Guide for FastAPI Backend

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **GitHub Repository**: Push your code to GitHub
3. **Environment Variables**: Prepare your API keys

## Files Created for Deployment

### 1. `vercel.json` - Vercel Configuration
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ],
  "env": {
    "OPENAI_API_KEY": "@openai_api_key",
    "QDRANT_URL": "@qdrant_url",
    "QDRANT_API_KEY": "@qdrant_api_key",
    "ANSWER_EXTRACTION_MODEL": "@answer_extraction_model"
  }
}
```

### 2. `api/index.py` - Vercel Entry Point
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Import your main app
from main import app

# Configure CORS for Vercel deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this with your frontend domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vercel requires the app to be named 'app' or 'handler'
handler = app
```

### 3. `requirements.txt` - Python Dependencies
Updated with specific versions for better compatibility.

### 4. `runtime.txt` - Python Version
Specifies Python 3.11 for the deployment.

## Deployment Steps

### Step 1: Prepare Your Repository

1. **Initialize Git** (if not already done):
```bash
git init
git add .
git commit -m "Initial commit for Vercel deployment"
```

2. **Push to GitHub**:
```bash
git remote add origin https://github.com/yourusername/your-repo-name.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Vercel

#### Option A: Vercel CLI (Recommended)

1. **Install Vercel CLI**:
```bash
npm install -g vercel
```

2. **Login to Vercel**:
```bash
vercel login
```

3. **Deploy**:
```bash
cd c:/Users/jaina/final_serach_project/backend
vercel
```

4. **Follow the prompts**:
   - Link to existing project? No
   - Project name: `your-project-name`
   - Directory: `./` (current directory)
   - Override settings? No

#### Option B: Vercel Dashboard

1. **Go to [vercel.com/dashboard](https://vercel.com/dashboard)**
2. **Click "New Project"**
3. **Import your GitHub repository**
4. **Configure the project**:
   - Framework Preset: `Other`
   - Root Directory: `./` (or leave empty)
   - Build Command: (leave empty)
   - Output Directory: (leave empty)
   - Install Command: `pip install -r requirements.txt`

### Step 3: Configure Environment Variables

In your Vercel dashboard, go to **Settings > Environment Variables** and add:

1. **OPENAI_API_KEY**
   - Value: Your OpenAI API key
   - Environment: Production, Preview, Development

2. **QDRANT_URL**
   - Value: Your Qdrant cloud URL (e.g., `https://your-cluster.qdrant.cloud`)
   - Environment: Production, Preview, Development

3. **QDRANT_API_KEY**
   - Value: Your Qdrant API key
   - Environment: Production, Preview, Development

4. **ANSWER_EXTRACTION_MODEL**
   - Value: `ft:gpt-3.5-turbo-0125:srmd:satsang-search-v1:BgoxJBWJ`
   - Environment: Production, Preview, Development

### Step 4: Test Your Deployment

1. **Get your deployment URL** (something like `https://your-project.vercel.app`)

2. **Test the API**:
```bash
curl https://your-project.vercel.app/
```

3. **Test specific endpoints**:
```bash
# Health check
curl https://your-project.vercel.app/health

# List transcripts
curl https://your-project.vercel.app/transcripts
```

## Important Notes

### File Upload Limitations

⚠️ **Vercel has limitations for file uploads**:
- **Serverless function timeout**: 10 seconds (hobby plan), 60 seconds (pro plan)
- **Request body size**: 4.5MB max
- **Memory limit**: 1024MB (hobby plan), 3008MB (pro plan)

For large file uploads, consider:
1. **Client-side chunking**: Split large files into smaller chunks
2. **External storage**: Upload files to AWS S3, Google Cloud Storage, etc.
3. **Background processing**: Use Vercel Edge Functions or external workers

### Database Considerations

✅ **Your current setup works well**:
- **Qdrant Cloud**: External vector database (✓ Recommended)
- **OpenAI API**: External API calls (✓ Compatible)

### Performance Optimization

1. **Cold Start Optimization**:
```python
# Add to your main.py
@app.on_event("startup")
async def startup_event():
    # Pre-warm connections
    pass
```

2. **Caching**: Consider Redis or Vercel KV for caching results

3. **Connection Pooling**: Use connection pooling for external services

## Troubleshooting

### Common Issues

1. **Import Errors**:
   - Ensure all dependencies are in `requirements.txt`
   - Check Python version compatibility

2. **Environment Variables**:
   - Verify all environment variables are set in Vercel dashboard
   - Check variable names match exactly

3. **Timeout Issues**:
   - Large file processing might timeout
   - Consider implementing async processing

4. **CORS Issues**:
   - Update CORS origins in `api/index.py`
   - Add your frontend domain to allowed origins

### Debug Deployment

1. **Check Vercel logs**:
   - Go to your project dashboard
   - Click on "Functions" tab
   - View function logs

2. **Local testing**:
```bash
# Test locally with Vercel
vercel dev
```

## Frontend Integration

Update your frontend to use the new Vercel URL:

```javascript
// Replace localhost with your Vercel URL
const API_BASE_URL = 'https://your-project.vercel.app';

// Update all API calls
const response = await fetch(`${API_BASE_URL}/transcripts/example.srt/extract-entities`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    use_ai: true,
    include_statistics: true
  })
});
```

## Security Considerations

1. **CORS Configuration**:
```python
# In production, specify your frontend domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend-domain.com",
        "https://your-app.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

2. **API Rate Limiting**: Consider implementing rate limiting

3. **Input Validation**: Your Pydantic models provide good validation

## Monitoring and Analytics

1. **Vercel Analytics**: Enable in project settings
2. **Custom Logging**: Add structured logging for better debugging
3. **Error Tracking**: Consider integrating Sentry or similar

## Cost Optimization

1. **Vercel Pricing**:
   - Hobby: Free (with limitations)
   - Pro: $20/month per user
   - Enterprise: Custom pricing

2. **Usage Monitoring**:
   - Track function invocations
   - Monitor bandwidth usage
   - Optimize for cold starts

## Next Steps

1. **Deploy and test** your application
2. **Configure custom domain** (optional)
3. **Set up monitoring** and error tracking
4. **Optimize performance** based on usage patterns
5. **Implement CI/CD** with GitHub Actions (optional)

Your FastAPI backend is now ready for production deployment on Vercel! 🚀
