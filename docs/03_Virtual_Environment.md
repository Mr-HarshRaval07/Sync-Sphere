# Virtual Environment

## 1. Concept

A virtual environment creates an isolated Python environment for a project.

## 2. Why?

- Avoids package conflicts.
- Keeps dependencies project-specific.

## 3. Diagram

Computer
│
├── Project A
│   └── venv
│
├── Project B
│   └── venv
│
└── Sync Sphere
    └── venv

## 4. Key Notes

- Every project should have its own venv.
- Installed packages stay inside the venv.
- Do not upload venv to GitHub.

## 5. Viva Questions

Q1. What is a virtual environment?

Q2. Why do we use venv?