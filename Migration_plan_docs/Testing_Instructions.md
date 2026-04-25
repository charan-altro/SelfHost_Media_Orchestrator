# Testing the Go+Wails Migration

The foundational backend has been successfully migrated to Go. The database schema uses `GORM`, and the filesystem scanner has been translated to use fast Go coroutines (`goroutines`). 

Wails wraps your existing `frontend/` React/Vite application natively, meaning your UI remains exactly the same but runs as a true desktop app.

Here is how you can test the new application on your Windows machine:

## Step 1: Install Wails (If not already installed)
Since this uses Wails, you must have the Wails CLI installed globally in Go.
Open your PowerShell or Command Prompt and run:
```powershell
go install github.com/wailsapp/wails/v2/cmd/wails@latest
```

## Step 2: Download Go Dependencies
Navigate to your project root where the new `go.mod` was created:
```powershell
cd c:\Users\chara\New_Projects_antigravity\SelfHost_Media_Orchestrator_python
go mod tidy
```
This will download `gorm`, `sqlite`, and the Wails v2 framework dependencies.

## Step 3: Start Development Mode
You can now spin up the entire application (both the Vite frontend and Go backend) in hot-reload mode:
```powershell
wails dev
```
### What happens when you run this?
1. Wails will read `wails.json`.
2. It will automatically run `npm install` and `npm run dev` in your `frontend/` folder.
3. It will compile the Go backend.
4. It will open a Native Windows App Window containing your React UI.

## Step 4: Connecting React to Go (Frontend Update)
Currently, your React app makes REST API calls to `http://localhost:8000`. You need to switch these to call the Go backend directly using the auto-generated bindings. 

When you run `wails dev`, Wails generates a `frontend/wailsjs/` folder containing javascript representations of your Go functions. 

In your React files (e.g., `frontend/src/components/Libraries.jsx`), change your fetching logic:

**Old Way (Python REST):**
```javascript
fetch('/api/libraries')
  .then(res => res.json())
  .then(data => setLibraries(data));
```

**New Way (Native Go Wails):**
```javascript
import { GetLibraries, ScanLibrary } from '../../wailsjs/go/main/App';
import { EventsOn } from '../../wailsjs/runtime/runtime';

// Fetch libraries natively
GetLibraries().then(data => setLibraries(data));

// Trigger a scan natively
ScanLibrary(1).then(message => console.log(message));

// Listen for scan progress events emitted from Go
EventsOn('scan-progress', (data) => {
  console.log(`Library ${data.library_id} scan progress: ${data.progress}%`);
});
```

## Step 5: Build the Production Executable
Once you've updated your frontend to use the native Go calls and verified everything works, you can build the final standalone `.exe` (which was the primary goal of this conversion!).

Stop the dev server (`Ctrl+C`), and run:
```powershell
wails build -platform windows/amd64
```
You will find your fully compiled, standalone `MediaOrchestrator.exe` in the `build/bin/` folder. You can now distribute this single file without requiring Node.js, Python, or Docker!
