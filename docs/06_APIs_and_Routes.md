# APIs and Routes

## 1. Concept

An API is a way for applications to communicate.

A Route is a URL that performs a specific action.

## 2. Why?

- Frontend communicates with backend.
- Backend communicates with third-party applications.
- Every feature starts with an API route.

## 3. Diagram

Browser
   │
GET /
   │
   ▼
FastAPI Route
   │
home()
   │
   ▼
JSON Response

## 4. Key Notes

- API = Communication interface.
- Route = URL endpoint.
- Every route performs one task.
- FastAPI converts Python objects into JSON.