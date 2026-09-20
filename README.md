# Digispark Upload Lab

A small FastAPI application for a controlled local lab.

It provides:

- `POST /api/upload` for authenticated multipart file uploads.
- A minimal browser UI at `/`.
- A received-file list with downloads.
- `GET /health` for Docker health checks.
- Persistent Docker storage in `./data/uploads`.
- File-extension and size limits.

The default configuration only accepts `.txt` files.

## 1. Configure

Copy the example environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and replace:

```text
UPLOAD_API_KEY=replace-with-a-long-random-lab-key
```

with a private lab key.

## 2. Start with Docker

```bash
docker compose up -d --build
```

Open:

```text
http://localhost:8080
```

API documentation:

```text
http://localhost:8080/docs
```

Health endpoint:

```text
http://localhost:8080/health
```

## 3. Upload from PowerShell

Replace the URL and API key as required:

```powershell
$Server = "http://127.0.0.1:8080/api/upload"
$ApiKey = "your-lab-key"
$File = "C:\DigisparkLab\outbox\test1.txt"

curl.exe `
  --fail `
  -X POST `
  -H "X-API-Key: $ApiKey" `
  -F "file=@$File" `
  $Server
```

## 4. Upload every `.txt` file from the explicit lab folder

This example intentionally uses only the dedicated test directory:

```powershell
$Server = "http://127.0.0.1:8080/api/upload"
$ApiKey = "your-lab-key"
$Folder = "C:\DigisparkLab\outbox"

Get-ChildItem -Path $Folder -File -Filter "*.txt" | ForEach-Object {
    Write-Host "Uploading $($_.Name)..."

    curl.exe `
        --fail `
        --silent `
        --show-error `
        -X POST `
        -H "X-API-Key: $ApiKey" `
        -F "file=@$($_.FullName)" `
        $Server

    Write-Host ""
}
```

## 5. Stop

```bash
docker compose down
```

Uploaded files remain in:

```text
data/uploads/
```

To also remove the locally stored test files, delete that directory's contents manually.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_TITLE` | `Digispark Upload Lab` | UI/service title |
| `APP_PORT` | `8080` | Host port exposed by Compose |
| `UPLOAD_API_KEY` | `change-me` | API authentication key |
| `UPLOAD_DIR` | `/data/uploads` | Container storage path |
| `MAX_FILE_SIZE_MB` | `5` | Per-file size limit |
| `ALLOWED_EXTENSIONS` | `.txt` | Comma-separated allowed extensions |

Example:

```text
ALLOWED_EXTENSIONS=.txt,.log
```

## Project structure

```text
digispark-upload-lab/
├── app/
│   ├── main.py
│   ├── static/
│   │   └── style.css
│   └── templates/
│       └── index.html
├── data/
│   └── uploads/
│       └── .gitkeep
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Lab scope

The server is designed for an explicit test workflow. Keep the PowerShell client scoped to a dedicated folder such as:

```text
C:\DigisparkLab\outbox
```

instead of searching user folders or the rest of the filesystem.
