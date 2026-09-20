# Digispark Upload Lab — FastAPI Backend

Final documentation for the FastAPI backend used in the Digispark lab project.

This service was built for a controlled test environment where predefined test files are sent over HTTPS to a backend, stored persistently, and managed through a lightweight web dashboard.

> This project is intended only for lab use with synthetic test data. The client side should operate only on an explicitly defined test directory and should not be used to search or collect real user files.

---

## 1. Architecture Overview

The overall flow is:

```text
Digispark
   ↓
USB HID
   ↓
Windows
   ↓
PowerShell
   ↓
HTTPS Request
   ↓
FastAPI Backend
   ↓
Persistent Storage
   ↓
Web Dashboard
```

The Digispark itself does not read files and does not connect directly to the network.

Its role is limited to acting as a USB keyboard and triggering a predefined workflow on the Windows host.

The FastAPI backend is responsible for receiving, validating, storing, exposing, and managing the uploaded test files.

---

## 2. Backend Features

The final backend includes:

- REST-based file upload
- API key authentication for uploads
- File extension restrictions
- Maximum file size validation
- Temporary-file handling before final storage
- Persistent storage
- Web dashboard
- Manual upload from the dashboard
- File count and storage usage display
- File download
- Per-file deletion with an admin key
- Delete-all operation with an admin key
- Health check endpoint
- Automatic FastAPI Swagger documentation
- Docker support
- Deployment behind a reverse proxy and HTTPS

---

## 3. API Endpoints

### `GET /`

Main web dashboard.

The dashboard can be used to:

- View uploaded files
- See the total number of files
- Check total storage usage
- Download stored files
- Upload test files manually
- Delete a single file using the admin key
- Delete all test files using the admin key

---

### `POST /api/upload`

Main upload endpoint used by the client.

Authentication is provided through the following HTTP header:

```http
X-API-Key: YOUR_UPLOAD_API_KEY
```

Example request:

```bash
curl -X POST \
  -H "X-API-Key: YOUR_UPLOAD_API_KEY" \
  -F "file=@test.txt" \
  https://example.com/api/upload
```

Example successful response:

```json
{
  "success": true,
  "filename": "test.txt",
  "size": 1024,
  "size_human": "1.0 KB"
}
```

If the API key is invalid:

```http
401 Unauthorized
```

---

### `POST /ui/upload`

Manual upload route used by the web dashboard.

The upload API key is submitted through the form and the file is stored only after validation succeeds.

---

### `GET /files/{filename}`

Downloads a stored file.

Example:

```text
/files/test.txt
```

If the file does not exist:

```http
404 Not Found
```

---

### `POST /ui/delete/{filename}`

Deletes one specific file from the dashboard.

This operation requires an `Admin Key`.

The admin credential is intentionally separate from the upload credential.

---

### `POST /ui/delete-all`

Deletes all allowed test files from the storage directory.

The backend limits this action to files that:

- are regular files
- are not temporary upload files
- have an allowed extension

This route also requires the `Admin Key`.

---

### `GET /health`

Health check endpoint.

Example response:

```json
{
  "status": "ok",
  "service": "Digispark Upload Lab",
  "allowed_extensions": [
    ".txt"
  ],
  "max_file_size_mb": 5
}
```

This endpoint can also be used by Docker or the deployment platform for service health checks.

---

### `GET /docs`

FastAPI automatically exposes interactive Swagger documentation at:

```text
https://example.com/docs
```

---

## 4. File Validation

The backend performs several checks before accepting a file.

### Filename Validation

The uploaded filename is normalized using:

```python
Path(filename).name
```

This strips unexpected path information from the submitted filename.

Invalid filenames are rejected.

### Extension Validation

The file extension must exist in the configured `ALLOWED_EXTENSIONS` list.

Default:

```text
.txt
```

### File Size Validation

Maximum file size is controlled through:

```text
MAX_FILE_SIZE_MB
```

Default:

```text
5 MB
```

If a file exceeds the configured limit, the server returns:

```http
413 Payload Too Large
```

---

## 5. File Storage Strategy

Files are not written directly to the final destination.

The backend first writes the incoming upload to a temporary file:

```text
.filename.uploading
```

The stream is processed in chunks instead of loading the entire file into memory at once.

After the upload completes successfully, the temporary file is atomically moved into its final location.

This prevents incomplete uploads from appearing as valid files if the transfer fails midway.

---

## 6. Authentication Model

The project uses two separate credentials.

### Upload API Key

Used for file uploads:

```env
UPLOAD_API_KEY=replace-with-a-long-random-key
```

### Admin Key

Used for administrative operations such as deleting files:

```env
ADMIN_KEY=replace-with-a-different-long-random-key
```

Separating these credentials means a client that is allowed to upload files does not automatically receive permission to perform destructive administrative actions.

Credential comparison is performed using:

```python
secrets.compare_digest()
```

---

## 7. Environment Variables

Main application settings:

| Variable | Default | Description |
|---|---|---|
| `APP_TITLE` | `Digispark Upload Lab` | Application title |
| `UPLOAD_API_KEY` | `change-me` | Upload authentication key |
| `ADMIN_KEY` | empty | Administrative key |
| `MAX_FILE_SIZE_MB` | `5` | Maximum file size |
| `UPLOAD_DIR` | `/data/uploads` | Storage path inside the container |
| `ALLOWED_EXTENSIONS` | `.txt` | Allowed file extensions |

Example:

```env
APP_TITLE=Digispark Upload Lab
UPLOAD_API_KEY=replace-with-a-long-random-upload-key
ADMIN_KEY=replace-with-a-different-long-random-admin-key
MAX_FILE_SIZE_MB=5
UPLOAD_DIR=/data/uploads
ALLOWED_EXTENSIONS=.txt
```

The real `.env` file should never be committed to the Git repository.

---

## 8. Running with Docker

Build and start the service:

```bash
docker compose up -d --build
```

Check running containers:

```bash
docker compose ps
```

Follow logs:

```bash
docker compose logs -f
```

Stop the service:

```bash
docker compose down
```

---

## 9. Persistent Storage

Uploaded files are stored inside the container at:

```text
/data/uploads
```

This path should be mapped to a Docker volume or bind mount so files survive container restarts and recreations.

---

## 10. CI/CD Flow

The repository can be connected to GitHub Actions for image builds and publishing.

Final deployment flow:

```text
Push to main
      ↓
GitHub Actions
      ↓
Build Docker Image
      ↓
Publish Image
      ↓
GitHub Container Registry
      ↓
Server / Arcane
      ↓
Docker Container
      ↓
Reverse Proxy
      ↓
HTTPS
```

In this setup, the application does not need to be built directly on the production server.

The server runs a prebuilt container image instead.

---

## 11. Reverse Proxy

For remote deployment, FastAPI should preferably not be exposed directly to the public internet.

Recommended layout:

```text
Internet
   ↓
HTTPS
   ↓
Reverse Proxy
   ↓
Docker Network
   ↓
FastAPI Container
```

TLS termination is handled by the reverse proxy, while the FastAPI application remains inside the internal Docker network.

---

## 12. Project Structure

```text
digispark-upload-lab/
├── app/
│   ├── main.py
│   ├── static/
│   │   └── style.css
│   └── templates/
│       └── index.html
│
├── data/
│   └── uploads/
│
├── .env.example
├── .gitignore
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 13. FastAPI's Role in the Project

FastAPI acts as the main boundary between the client workflow and persistent storage.

Its responsibilities can be summarized as:

```text
Receive Request
      ↓
Authenticate
      ↓
Validate Filename
      ↓
Validate Extension
      ↓
Stream File
      ↓
Check File Size
      ↓
Temporary Storage
      ↓
Atomic Replace
      ↓
Persistent Storage
      ↓
Expose Through Dashboard
```

The Digispark only starts the workflow.

The main file handling, validation, authentication, storage, and management logic lives in the backend.

---

## 14. Lab Scope

The client side should only operate on a dedicated test directory, for example:

```text
C:\DigisparkLab\outbox
```

Example synthetic files:

```text
test-01.txt
test-02.txt
demo.txt
```

The purpose of the project is to practice the interaction between:

- Embedded systems
- USB HID
- Operating system automation
- HTTP
- REST APIs
- Authentication
- File handling
- Docker
- CI/CD
- Reverse proxies
- Deployment

It is not intended for collecting real user files.

---

## 15. Tech Stack

```text
Python
FastAPI
Uvicorn
Jinja2
HTML / CSS
Docker
Docker Compose
GitHub Actions
GitHub Container Registry
Reverse Proxy
HTTPS
```

---

## Version

```text
FastAPI Application Version: 1.1.0
```
