# Sync-Sphere-
AI-powered Agent Integration Platform using MCP, RAG, Vector Search, and FastAPI.

## Backend database setup

1. Open `backend/.env`.
2. Set `MONGO_URI` to your MongoDB Atlas connection string.
   Example:
   ```
   MONGO_URI=mongodb+srv://<username>:<password>@<cluster-address>.mongodb.net/syncsphere?retryWrites=true&w=majority
   DB_NAME=syncsphere
   ```
3. Restart the backend server.
4. Verify with `GET /db-status` on the backend.
