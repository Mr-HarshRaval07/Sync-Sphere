# First FastAPI Application

## 1. Concept

A FastAPI application is the backend server that receives requests and returns responses.

## 2. Why?

- Accept requests from frontend.
- Execute business logic.
- Connect databases and APIs.
- Return data.

## 3. Diagram

Browser
   │
HTTP Request
   │
   ▼
FastAPI Server
   │
Returns Response
   │
Browser

## 4. Key Notes

- FastAPI starts with a FastAPI object.
- Routes define application endpoints.
- Uvicorn runs the server.