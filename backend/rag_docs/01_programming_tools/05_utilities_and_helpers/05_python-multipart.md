# python-multipart

[python-multipart](https://github.com/andrew-d/python-multipart) is a streaming multipart parser for Python, used for handling form data and file uploads.

### Why python-multipart?

- **Multipart Form Data Parsing:** Essential for handling file uploads (audio tracks) in web requests.
- **Streaming Support:** Efficiently processes large files without loading entire content into memory.
- **Integration with FastAPI:** Works seamlessly with FastAPI's request handling.

### How it's used in this project

- Parses audio file uploads sent from the frontend to the backend.
- Supports receiving metadata and audio content as multipart/form-data in API endpoints.
