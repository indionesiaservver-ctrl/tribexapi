# 🚀 Deploying to Coolify (Docker Method)

This is the most reliable way to get your API live. Follow these steps exactly.

## 1. Update Coolify Configuration
- Go to your application in the **Coolify Dashboard**.
- Go to the **Configuration** tab.
- Change **Build Pack** from `Nixpacks` to **`Docker`**.
- Click **Save**.

## 2. Environment Variables
Ensure these are set in the **Environment Variables** tab:
- `PORT`: `5000`
- `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION`: `python`

## 3. Network Setup
- **Exposed Port**: Ensure this is set to **`5000`**.

## 4. Push and Deploy
- **Push the new `Dockerfile`** to your GitHub repository.
- Click **Deploy** in Coolify.

---

### 💡 Why this works:
1.  **Guaranteed Dependencies**: The `Dockerfile` manually installs `gcc` and `python-dev`, which are sometimes missing in automatic builds.
2.  **No Cache Issues**: Docker ignores Nixpacks' cached layers, giving you a fresh, clean build.
3.  **Correct Library**: It uses the fixed `requirements.txt` with `protobuf 5.29.3`.

**Once it's done, your API will be live on port 5000!** 🏁
