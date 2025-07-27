# Uvicorn

[Uvicorn](https://www.uvicorn.org/) is a lightning-fast ASGI server implementation, using `uvloop` and `httptools`. It is commonly used to serve asynchronous Python web frameworks such as FastAPI.

### Why Uvicorn?

- **Asynchronous Server:** Supports high-performance asynchronous communication, essential for FastAPI’s async capabilities.
- **Production Ready:** Suitable for running your app in production environments.
- **Easy Integration:** Seamlessly runs FastAPI apps with minimal configuration.
- **Hot Reload Support:** Enables automatic server reload during development.

### How it's used in this project

- Runs the FastAPI backend, serving HTTP requests and managing event loops.
- Handles concurrent client connections efficiently for file uploads, chat messages, and AI feedback generation.
