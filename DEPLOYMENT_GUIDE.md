# 🌐 Cloud Deployment Guide for Polygon MCP Server

Deploy your Polygon MCP Server to the cloud so Scira MCP Chat can access it remotely.

## 🚀 **Option 1: Railway (Recommended - Free)**

### **Step 1: Prepare for Railway**
```bash
# Install Railway CLI (optional)
npm install -g @railway/cli

# Or use the web interface at railway.app
```

### **Step 2: Deploy to Railway**
1. **Go to**: https://railway.app
2. **Sign up/Login** with GitHub
3. **Create New Project** → **Deploy from GitHub repo**
4. **Connect your repository** (or upload files)
5. **Set Environment Variables**:
   - `POLYGON_API_KEY` = `5b9gXwiZEx2kskt24s35eIHMpS2aAgPI`
   - `PORT` = `8000`
6. **Deploy** - Railway will auto-detect Python and deploy

### **Your Live URL**: 
`https://your-app-name.railway.app/sse`

---

## 🌊 **Option 2: Render (Free Tier)**

### **Step 1: Deploy to Render**
1. **Go to**: https://render.com
2. **Sign up/Login**
3. **New** → **Web Service**
4. **Connect GitHub** or **Upload files**
5. **Settings**:
   - **Build Command**: `uv sync`
   - **Start Command**: `uv run polygon_mcp_server_sse.py`
   - **Environment Variables**:
     - `POLYGON_API_KEY` = `5b9gXwiZEx2kskt24s35eIHMpS2aAgPI`

### **Your Live URL**: 
`https://your-app-name.onrender.com/sse`

---

## ☁️ **Option 3: Heroku**

### **Step 1: Prepare Heroku Files**
```bash
# Create Procfile
echo "web: uv run polygon_mcp_server_sse.py" > Procfile

# Create runtime.txt
echo "python-3.11.11" > runtime.txt
```

### **Step 2: Deploy to Heroku**
```bash
# Install Heroku CLI
# Then:
heroku create your-polygon-mcp-server
heroku config:set POLYGON_API_KEY=5b9gXwiZEx2kskt24s35eIHMpS2aAgPI
git add .
git commit -m "Deploy Polygon MCP Server"
git push heroku main
```

### **Your Live URL**: 
`https://your-polygon-mcp-server.herokuapp.com/sse`

---

## 🐳 **Option 4: Docker + Any Cloud**

### **Step 1: Build Docker Image**
```bash
# Build the image
docker build -t polygon-mcp-server .

# Test locally
docker run -p 8000:8000 -e POLYGON_API_KEY=5b9gXwiZEx2kskt24s35eIHMpS2aAgPI polygon-mcp-server
```

### **Step 2: Deploy to Cloud**
- **Google Cloud Run**
- **AWS ECS**
- **Azure Container Instances**
- **DigitalOcean App Platform**

---

## 🔧 **Option 5: Vercel (Serverless)**

### **Step 1: Create vercel.json**
```json
{
  "builds": [
    {
      "src": "polygon_mcp_server_sse.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "polygon_mcp_server_sse.py"
    }
  ],
  "env": {
    "POLYGON_API_KEY": "5b9gXwiZEx2kskt24s35eIHMpS2aAgPI"
  }
}
```

### **Step 2: Deploy**
```bash
npx vercel --prod
```

---

## 🎯 **Quick Deploy (1-Click Options)**

### **Railway (Fastest)**
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

### **Render**
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### **Heroku**
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

---

## 🔗 **Connecting to Scira MCP Chat**

Once deployed, use your live URL in Scira:

### **SSE Endpoint**: `https://your-domain.com/sse`
### **Environment Variables**: 
- `API_KEY` = `5b9gXwiZEx2kskt24s35eIHMpS2aAgPI`

---

## 🧪 **Testing Your Deployment**

### **Health Check**
```bash
curl https://your-domain.com/health
# Should return: {"status": "healthy", "service": "polygon-mcp-server"}
```

### **SSE Endpoint**
```bash
curl https://your-domain.com/sse
# Should return MCP server info
```

---

## 🛠️ **Troubleshooting**

### **Common Issues:**
1. **Port binding**: Make sure `PORT` environment variable is set
2. **API Key**: Ensure `POLYGON_API_KEY` is set correctly
3. **Dependencies**: Check that `uv sync` runs successfully
4. **Health check**: Verify `/health` endpoint responds

### **Logs:**
- **Railway**: Check deployment logs in dashboard
- **Render**: View logs in service dashboard
- **Heroku**: `heroku logs --tail`

---

## 💡 **Recommended: Railway**

**Why Railway?**
- ✅ **Free tier** with generous limits
- ✅ **Auto-deployment** from GitHub
- ✅ **Built-in SSL** (HTTPS)
- ✅ **Environment variables** easy to set
- ✅ **Logs and monitoring** included
- ✅ **Custom domains** supported

**Perfect for MCP servers!** 🚀 