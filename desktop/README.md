# AI Coding Mentor Desktop

The desktop app is the existing React/Vite mentor workspace packaged with Pake/Tauri. There is no second desktop UI.

## Build

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-desktop.ps1
```

The script builds the frontend and packages `frontend/dist` as a native Windows x64 app.

Pake supports local directories as package inputs and exposes Windows x64, tray, hide-on-close, always-on-top and window-decoration controls. This project uses those features only as the native shell; all mentor logic remains in the main application.

## Run

Start the local infrastructure:

```powershell
docker compose up --build -d
```

Then run the generated executable under `desktop/`.

For the OS-level floating mentor that can sit over VS Code or another editor, use the optional companion:

```powershell
.\.venv-overlay\Scripts\Activate.ps1
python desktop_overlay/app.py --server http://127.0.0.1:8000 --language python --watch
```

## Architecture

```text
AI Coding Mentor.exe
    |
    +-- Pake/Tauri WebView
    |    +-- React + Monaco
    |    +-- WebSocket analysis
    |    +-- execution/tests
    |    +-- mentor + analytics
    |
    +-- localhost:8000 FastAPI
         +-- analysis
         +-- mentor / LLM
         +-- persistence
         +-- screen / OCR
         +-- sandbox runner :8100
```

Packaging does not bundle Docker, PostgreSQL, the model server or the sandbox images. Those remain local services.

## Important

For the first desktop release, Windows x64 is the primary target. The same Pake config is portable to macOS/Linux after their native prerequisites are installed.