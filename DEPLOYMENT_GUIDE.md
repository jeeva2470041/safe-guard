# Complete Deployment Guidelines: Vercel, Render & MongoDB Atlas
## Agent Guard (SafeAI) Production Hosting Manual

This guide provides end-to-end instructions for deploying Agent Guard:
- **Database**: MongoDB Atlas (Free Cloud Cluster)
- **Backend**: Render (FastAPI Web Service)
- **Frontend**: Vercel (React 19 + Vite SPA)
- **IDE Bridge**: Google Antigravity PreToolUse Hook Integration

---

## 🏗️ Architecture Overview

```
[ Developer in Google Antigravity / Browser ]
           │
           ├──────────────────────────────┐
           ▼                              ▼
[ Vercel Frontend SPA ]        [ Local Antigravity Hook ]
(https://safeai.vercel.app)    (PreToolUse / PreInvocation)
           │                              │
           └──────────────┬───────────────┘
                          │ HTTPS / JSON
                          ▼
            [ Render Backend Web Service ]
           (https://safeai-api.onrender.com)
                          │ Motor (Async)
                          ▼
            [ MongoDB Atlas Cloud DB ]
           (Collection: goals, actions, logs)
```

---

## Step 1: MongoDB Atlas Setup (Cloud Database)

Agent Guard requires MongoDB to persist dynamic goals, version histories, intercepted actions, and audit logs.

### 1.1 Create Free MongoDB Atlas Account & Cluster
1. Visit [mongodb.com/atlas](https://www.mongodb.com/cloud/atlas) and sign in/register.
2. Click **"Create a deployment"** $\rightarrow$ choose **M0 Free Shared Cluster**.
3. Choose your preferred cloud provider and region (e.g., AWS / `us-east-1` or `ap-south-1`).
4. Click **"Create"**.

### 1.2 Configure Database User & Security Access
1. Under **Database Access** $\rightarrow$ click **"Add New Database User"**:
   - Authentication Method: **Password**
   - Username: `agent_guard_admin` (or your choice)
   - Password: `<secure-password>`
   - Database User Privileges: **Read and write to any database**
   - Click **"Add User"**.
2. Under **Network Access** $\rightarrow$ click **"Add IP Address"**:
   - Select **"Allow Access from Anywhere"** (`0.0.0.0/0`) so that Render can connect dynamically.
   - Click **"Confirm"**.

### 1.3 Obtain Connection URI
1. Go to **Database** $\rightarrow$ click **"Connect"** on your cluster.
2. Choose **"Drivers"** (Python / Motor).
3. Copy your connection string:
   ```
   mongodb+srv://agent_guard_admin:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority
   ```
   *(Replace `<password>` with your actual database user password)*.

---

## Step 2: Backend Deployment on Render (FastAPI)

Deploy the Python FastAPI backend as a Render Web Service.

### Option A: Using Render Web Dashboard (Recommended)

1. Push your repository to **GitHub**.
2. Log in to [dashboard.render.com](https://dashboard.render.com).
3. Click **"New +"** $\rightarrow$ select **"Web Service"**.
4. Connect your GitHub repository: `your-username/safeai` (or `safe-guard`).
5. Configure the service settings:
   - **Name**: `agent-guard-backend` (or `safeai-api`)
   - **Language**: `Python`
   - **Region**: Select closest to your MongoDB Atlas region (e.g., `Oregon (US West)` or `Frankfurt`).
   - **Branch**: `main`
   - **Root Directory**: `agent-guard/backend` *(or leave blank if repository root is backend)*
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
     *(If Root Directory is left at root: `pip install -r agent-guard/backend/requirements.txt`)*
   - **Start Command**:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
     *(If Root Directory is left at root: `cd agent-guard/backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`)*
   - **Instance Type**: `Free`

6. Add **Environment Variables** under **"Advanced" / "Environment Variables"**:

   | Key | Value | Description |
   |---|---|---|
   | `MONGODB_URI` | `mongodb+srv://agent_guard_admin:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority` | Your MongoDB Atlas connection URI |
   | `DATABASE_NAME` | `agent_guard` | Database name |
   | `CORS_ORIGINS` | `*` | Or specify `https://your-app.vercel.app` |
   | `OPENAI_API_KEY` | `sk-...` *(Optional)* | For LLM-based policy synthesis (deterministic fallback works offline) |
   | `PYTHON_VERSION` | `3.11.9` | Python runtime version |

7. Click **"Create Web Service"**.
8. Wait 1–2 minutes for the build to complete. Once deployed, Render will provide your public backend URL:
   `https://agent-guard-backend.onrender.com`

### 2.2 Verify Backend Health
Open `https://agent-guard-backend.onrender.com/health` in your browser. You should see:
```json
{
  "status": "healthy"
}
```

---

## Step 3: Frontend Deployment on Vercel (React + Vite)

Deploy the React 19 + Vite dashboard on Vercel with automatic HTTPS and SPA routing.

### 3.1 Import Project to Vercel
1. Log in to [vercel.com](https://vercel.com).
2. Click **"Add New..."** $\rightarrow$ **"Project"**.
3. Select your GitHub repository (`safeai` or `safe-guard`) and click **"Import"**.

### 3.2 Configure Vercel Project Settings
1. **Framework Preset**: `Vite`
2. **Root Directory**: Click **Edit** $\rightarrow$ select `agent-guard/frontend`.
3. **Build and Output Settings**:
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Install Command: `npm install`
4. **Environment Variables**:
   - Add the following variable pointing to your deployed Render backend URL:

   | Key | Value |
   |---|---|
   | `VITE_API_BASE_URL` | `https://agent-guard-backend.onrender.com` |

   *(Ensure there is no trailing slash in the URL)*.

5. Click **"Deploy"**.

### 3.3 SPA Routing with `vercel.json`
The repository already includes `agent-guard/frontend/vercel.json`:
```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```
This ensures direct link navigation and page refreshes on Vercel route properly to the React SPA without 404 errors.

---

## Step 4: Google Antigravity Integration (Cloud & Local)

You can run Google Antigravity locally while pointing to either your local backend or your hosted Render backend.

### 4.1 Connecting Antigravity Hook to Render Backend
In `.agents/hooks.json`, the hooks execute `agent_guard_hook.py`.

To route Antigravity tool evaluations through your Render backend:
1. On your local machine, set the environment variable:
   - **Windows (PowerShell)**:
     ```powershell
     $env:AGENT_GUARD_API="https://safe-guard-backend-5hra.onrender.com/api/agent/intercept"
     $env:AGENT_GUARD_SESSION_API="https://safe-guard-backend-5hra.onrender.com/api/agent/session/start"
     ```
   - **Linux / macOS**:
     ```bash
     export AGENT_GUARD_API="https://agent-guard-backend.onrender.com/api/agent/intercept"
     export AGENT_GUARD_SESSION_API="https://agent-guard-backend.onrender.com/api/agent/session/start"
     ```
2. In `.agents/hooks.json`, enable the hook:
   ```json
   {
     "agent-guard-interceptor": {
       "enabled": true,
       "PreInvocation": [
         {
           "type": "command",
           "command": "python agent-guard/integrations/antigravity/agent_guard_preinvocation_hook.py",
           "timeout": 15
         }
       ],
       "PreToolUse": [
         {
           "matcher": "*",
           "hooks": [
             {
               "type": "command",
               "command": "python agent-guard/integrations/antigravity/agent_guard_hook.py",
               "timeout": 180
             }
           ]
         }
       ]
     }
   }
   ```

---

## Step 5: End-to-End Verification Checklist

| Checkpoint | Action | Expected Result |
|---|---|---|
| **1. Database Check** | Check MongoDB Atlas metrics | Connected, collections (`goals`, `actions`, `audit_logs`) initialized. |
| **2. Backend Health** | Visit `https://your-backend.onrender.com/health` | Returns `{"status": "healthy"}` |
| **3. API Documentation** | Visit `https://your-backend.onrender.com/docs` | Swagger UI loads with full `/api/goals` and `/api/actions` endpoints. |
| **4. Frontend Live** | Visit `https://your-frontend.vercel.app` | Agent Guard SOC Dashboard loads cleanly with glassmorphic dark theme. |
| **5. Scenario A Test** | Click **"Run Scenario A (Normal Flow)"** | Goal synthesizes, actions execute, rolling integrity stays at 98% (Green). |
| **6. Scenario B Test** | Click **"Run Scenario B (Goal Drift)"** | Agent drifts into backend $\rightarrow$ Action blocked $\rightarrow$ **"⏸ AGENT PAUSED"** modal appears. |
| **7. Goal Evolution** | In paused state, click **"MODIFY GOAL (V2)"** | Goal upgrades from V1 to V2, policy scope expands, agent resumes. |
| **8. Scenario C Test** | Click **"Run Scenario C (Security Violation)"** | Attacker attempts credential exfiltration $\rightarrow$ Instant blocked verdict + alert banner. |

---

## 🛠️ Troubleshooting Guide

### 1. Render Free Tier "Cold Start" (Spinning down after inactivity)
- **Symptom**: First request to Render takes 30–50 seconds to respond.
- **Fix**: Free Render web services sleep after 15 minutes of inactivity. For hackathons/demos, open the `/health` endpoint 1 minute before presenting to wake the instance, or ping with a free cron monitor like UptimeRobot (`https://uptimerobot.com`).

### 2. CORS Error on Vercel Dashboard
- **Symptom**: Browser console displays `Cross-Origin Request Blocked`.
- **Fix**: In Render backend environment variables, ensure `CORS_ORIGINS` is set to `*` or include your exact Vercel domain `https://<your-project>.vercel.app`.

### 3. MongoDB Connection Timeout
- **Symptom**: Backend logs show `ServerSelectionTimeoutError`.
- **Fix**: In MongoDB Atlas $\rightarrow$ **Network Access**, ensure `0.0.0.0/0` (Allow Access from Anywhere) is active.
