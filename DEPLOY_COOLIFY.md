# 🚀 Deploying to Coolify (Ubuntu VPS)

Follow these simple steps to deploy your FreeFire API to Coolify without Docker manually.

## 1. Create a New Resource
- Open your Coolify Dashboard.
- Click **+ New Resource** -> **Public Repository** (or Private if applicable).
- Paste your GitHub/GitLab repository URL.

## 2. Configure Build Settings
- **Build Pack**: Select **Nixpacks** (This is the "Direct" way).
- **Python Version**: Nixpacks will automatically use the version from `nixpacks.toml` (3.10).
- **Install Command**: `pip install -r requirements.txt` (Auto-detected).
- **Start Command**: `gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --worker-class gthread --timeout 120 index:app` (Auto-detected from `Procfile`).

## 3. Set Environment Variables
Go to the **Environment Variables** tab in Coolify and add:
- `PORT`: `5000`
- `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION`: `python`

## 4. Network Setup
- **Exposed Port**: Set this to `5000`.
- Coolify will automatically create a Reverse Proxy (Nginx) and give you a URL (e.g., `https://your-api.coolify.io`).

## 5. Deploy
- Click **Deploy**.
- Once the build is finished, your API will be live!

---

### 💡 Troubleshooting
- **Bad Gateway?** Make sure the **Exposed Port** in Coolify settings matches the `PORT` variable (default 5000).
- **Protobuf Error?** The `nixpacks.toml` includes a fix, but ensure `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python` is set in the environment variables.
