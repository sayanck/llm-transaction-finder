# Render Deployment Guide

## 🚀 Deploying to Render

This guide will help you deploy the LLM Transaction Pattern Finder to Render.

### Prerequisites

1. **GitHub Repository**: Push your code to a GitHub repository
2. **Render Account**: Sign up at [render.com](https://render.com)
3. **Gemini API Key**: Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Step 1: Deploy Backend

1. **Create New Web Service**:
   - Go to your Render dashboard
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure Backend Service**:
   ```
   Name: transaction-analyzer-backend
   Environment: Python 3
   Build Command: cd backend && pip install -r requirements.txt
   Start Command: cd backend && python main.py
   ```

3. **Environment Variables**:
   ```
   GEMINI_API_KEY=your_actual_gemini_api_key
   PORT=8000
   ```

4. **Advanced Settings**:
   - **Health Check Path**: `/health`
   - **Auto-Deploy**: Yes (for automatic deployments on git push)

### Step 2: Deploy Frontend

1. **Create New Static Site**:
   - Go to your Render dashboard
   - Click "New +" → "Static Site"
   - Connect your GitHub repository

2. **Configure Frontend Service**:
   ```
   Name: transaction-analyzer-frontend
   Build Command: cd frontend && npm install && npm run build
   Publish Directory: frontend/build
   ```

3. **Environment Variables**:
   ```
   REACT_APP_API_URL=https://transaction-analyzer-backend.onrender.com
   ```

### Step 3: Update CORS Settings

After deploying both services, update the backend CORS settings:

1. **Get your frontend URL** from Render dashboard
2. **Update backend environment variable**:
   ```
   ALLOWED_ORIGINS=https://your-frontend-url.onrender.com
   ```

### Step 4: Test Deployment

1. **Backend Health Check**:
   ```
   https://transaction-analyzer-backend.onrender.com/health
   ```

2. **Frontend Access**:
   ```
   https://transaction-analyzer-frontend.onrender.com
   ```

### Environment Variables Reference

#### Backend Environment Variables
```
GEMINI_API_KEY=your_gemini_api_key_here
PORT=8000
ALLOWED_ORIGINS=https://your-frontend-url.onrender.com
```

#### Frontend Environment Variables
```
REACT_APP_API_URL=https://transaction-analyzer-backend.onrender.com
```

### Troubleshooting

#### Common Issues

1. **Build Failures**:
   - Check that all dependencies are in `requirements.txt`
   - Ensure Python version compatibility
   - Verify file paths in build commands

2. **CORS Errors**:
   - Update `ALLOWED_ORIGINS` environment variable
   - Check that frontend URL is correctly configured

3. **API Key Issues**:
   - Verify `GEMINI_API_KEY` is set correctly
   - Check API key permissions and quotas

4. **File Upload Issues**:
   - Render has file system limitations
   - Consider using cloud storage for large files

#### Debugging

1. **Check Logs**:
   - Go to your service dashboard
   - Click "Logs" tab to see real-time logs

2. **Health Check**:
   - Use `/health` endpoint to verify service status

3. **API Documentation**:
   - Visit `https://your-backend-url.onrender.com/docs` for API docs

### Performance Considerations

#### Free Tier Limitations
- **Sleep Mode**: Free services sleep after 15 minutes of inactivity
- **Cold Start**: First request after sleep may take 30+ seconds
- **Resource Limits**: Limited CPU and memory

#### Upgrade Options
- **Starter Plan**: $7/month - No sleep mode, better performance
- **Standard Plan**: $25/month - More resources, better reliability

### Security Best Practices

1. **Environment Variables**:
   - Never commit API keys to repository
   - Use Render's environment variable system

2. **CORS Configuration**:
   - Only allow necessary origins
   - Use HTTPS in production

3. **API Rate Limiting**:
   - Consider implementing rate limiting for production use

### Monitoring

1. **Health Checks**:
   - Monitor `/health` endpoint
   - Set up alerts for service downtime

2. **Performance Monitoring**:
   - Track response times
   - Monitor API usage and costs

3. **Error Tracking**:
   - Check logs regularly
   - Monitor error rates

### Custom Domain (Optional)

1. **Add Custom Domain**:
   - Go to service settings
   - Add your domain
   - Update DNS records as instructed

2. **SSL Certificate**:
   - Render provides free SSL certificates
   - Automatically enabled for custom domains

### Backup and Recovery

1. **Code Backup**:
   - Keep your GitHub repository updated
   - Use version control best practices

2. **Data Backup**:
   - For production use, consider database integration
   - Implement regular data backups

### Cost Optimization

1. **Free Tier Usage**:
   - Monitor usage to stay within limits
   - Consider upgrading only when necessary

2. **Resource Management**:
   - Optimize code for better performance
   - Use caching where appropriate

## 🎉 Success!

Once deployed, your application will be available at:
- **Frontend**: `https://transaction-analyzer-frontend.onrender.com`
- **Backend**: `https://transaction-analyzer-backend.onrender.com`
- **API Docs**: `https://transaction-analyzer-backend.onrender.com/docs`

The application will automatically redeploy when you push changes to your main branch.
