const { app, BrowserWindow, ipcMain, shell, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const os = require('os');
const fs = require('fs');

let mainWindow;

// Detect platform
function getPlatform() {
    const platform = os.platform();
    if (platform === 'win32') return 'windows';
    if (platform === 'darwin') return 'mac';
    return 'linux';
}

function getPlatformLabel() {
    const p = getPlatform();
    if (p === 'windows') return 'Windows';
    if (p === 'mac') return 'macOS';
    return 'Linux';
}

// Check if server is running
async function checkServer() {
    try {
        const resp = await fetch('http://localhost:8000/api');
        const data = await resp.json();
        return data.message === '装了吗 API';
    } catch {
        return false;
    }
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 800,
        minHeight: 600,
        title: '装了吗 - 软件安装助手',
        icon: path.join(__dirname, 'icon.png'),
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        backgroundColor: '#faf9f7',
        show: false
    });

    // Load the web frontend
    mainWindow.loadURL('http://localhost:8000/app');

    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// IPC Handlers
ipcMain.handle('get-platform', () => {
    return {
        platform: getPlatform(),
        label: getPlatformLabel(),
        arch: os.arch(),
        release: os.release()
    };
});

ipcMain.handle('check-server', async () => {
    return await checkServer();
});

ipcMain.handle('execute-script', async (event, { script, type }) => {
    return new Promise((resolve, reject) => {
        const platform = getPlatform();
        const fs = require('fs');
        const os = require('os');
        const path = require('path');
        const { exec } = require('child_process');
        
        // Clean script
        const cleanScript = script
            .replace(/\x1b\[[0-9;]*m/g, '')
            .replace(/\u00A0/g, ' ')
            .trim();
        
        const ext = platform === 'windows' ? '.ps1' : '.sh';
        const scriptFile = path.join(os.tmpdir(), 'zhuangle_install' + ext);
        
        // Write with BOM for PowerShell UTF-8 support
        if (platform === 'windows') {
            fs.writeFileSync(scriptFile, '\ufeff' + cleanScript, 'utf8');
        } else {
            fs.writeFileSync(scriptFile, cleanScript, { mode: 0o755 });
        }
        
        let cmd;
        if (platform === 'windows') {
            cmd = 'start powershell.exe -NoExit -ExecutionPolicy Bypass -File "' + scriptFile + '"';
        } else if (platform === 'mac') {
            cmd = 'open -a Terminal "' + scriptFile + '"';
        } else {
            cmd = 'x-terminal-emulator -e bash "' + scriptFile + '"';
        }
        
        exec(cmd, (error) => {
            if (error) {
                reject(error.message);
            } else {
                resolve({ code: 0, stdout: '', stderr: '' });
            }
        });
    });
});

ipcMain.handle('open-external', async (event, url) => {
    await shell.openExternal(url);
});

ipcMain.handle('show-save-dialog', async (event, options) => {
    const result = await dialog.showSaveDialog(mainWindow, options);
    return result;
});

// App lifecycle
app.whenReady().then(() => {
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
