# Nano Agent MCP Server - Windows Installation Script
# PowerShell script for Windows users

param(
    [switch]$Quick,
    [switch]$NoClaudeDesktop
)

# Colors and formatting
function Write-Header { Write-Host $args[0] -ForegroundColor Blue -BackgroundColor White }
function Write-Step { Write-Host "▶ $($args[0])" -ForegroundColor Blue }
function Write-Success { Write-Host "✅ $($args[0])" -ForegroundColor Green }
function Write-Warning { Write-Host "⚠️  $($args[0])" -ForegroundColor Yellow }
function Write-Error { Write-Host "❌ $($args[0])" -ForegroundColor Red }

# Configuration
$InstallDir = "$env:USERPROFILE\.nano-agent"
$ConfigDir = "$env:USERPROFILE\.nano-cli"

Write-Header "🤖 Nano Agent MCP Server - Windows Installation"
Write-Host "=================================================" -ForegroundColor Blue
Write-Host ""

function Test-Requirements {
    Write-Step "Checking system requirements..."
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+\.\d+)") {
            $version = [version]$matches[1]
            if ($version -ge [version]"3.9") {
                Write-Success "Python $($matches[1]) found"
                return $true
            } else {
                Write-Error "Python 3.9+ required. Found: $($matches[1])"
                Write-Host "Please install Python 3.9+ from https://python.org"
                return $false
            }
        }
    } catch {
        Write-Error "Python not found"
        Write-Host "Please install Python 3.9+ from https://python.org"
        return $false
    }
}

function Install-UV {
    Write-Step "Installing uv package manager..."
    
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        Write-Success "uv already installed"
        return
    }
    
    try {
        # Download and run uv installer
        Invoke-WebRequest -Uri "https://astral.sh/uv/install.ps1" -UseBasicParsing | Invoke-Expression
        
        # Add to PATH for current session
        $uvPath = "$env:USERPROFILE\.cargo\bin"
        if (Test-Path $uvPath) {
            $env:PATH = "$uvPath;$env:PATH"
        }
        
        if (Get-Command uv -ErrorAction SilentlyContinue) {
            Write-Success "uv installed successfully"
        } else {
            Write-Error "uv installation failed"
            exit 1
        }
    } catch {
        Write-Error "Failed to install uv: $($_.Exception.Message)"
        exit 1
    }
}

function Install-NanoAgent {
    Write-Step "Installing Nano Agent..."
    
    # Create directories
    New-Item -Path $InstallDir -ItemType Directory -Force | Out-Null
    New-Item -Path $ConfigDir -ItemType Directory -Force | Out-Null
    
    # Copy current directory to install location (for development)
    $currentDir = Get-Location
    if (Test-Path "$currentDir\pyproject.toml") {
        Write-Step "Copying nano-agent files..."
        Copy-Item -Path $currentDir -Destination "$InstallDir\nano-agent" -Recurse -Force
    } else {
        Write-Error "Unable to find nano-agent source. Please run from nano-agent directory."
        exit 1
    }
    
    # Change to install directory
    Set-Location "$InstallDir\nano-agent\apps\nano_agent_mcp_server"
    
    # Copy environment file
    if ((Test-Path ".env.sample") -and !(Test-Path ".env")) {
        Copy-Item ".env.sample" ".env"
        Write-Success "Created .env file"
    }
    
    # Install dependencies and tool
    Write-Step "Installing dependencies..."
    uv sync
    uv tool install --force .
    
    Write-Success "Nano Agent installed"
}

function Setup-Configuration {
    Write-Step "Setting up configuration..."
    
    # Create default config
    $config = @{
        default_model = "gpt-oss:20b"
        default_provider = "ollama"
        default_temperature = 0.7
        default_max_tokens = 4000
    } | ConvertTo-Json -Depth 3
    
    $config | Out-File -FilePath "$ConfigDir\config.json" -Encoding UTF8
    Write-Success "Configuration created at $ConfigDir\config.json"
}

function Setup-ClaudeDesktop {
    if ($NoClaudeDesktop) {
        return
    }
    
    Write-Step "Setting up Claude Desktop integration..."
    
    # Find Claude Desktop config directory
    $claudeConfigDir = "$env:APPDATA\Claude"
    New-Item -Path $claudeConfigDir -ItemType Directory -Force | Out-Null
    
    # Get nano-agent path
    $nanoAgentPath = Get-Command nano-agent -ErrorAction SilentlyContinue
    if ($nanoAgentPath) {
        $nanoAgentCmd = "nano-agent"
    } else {
        $toolDir = uv tool dir
        $nanoAgentCmd = "$toolDir\Scripts\nano-agent.exe"
    }
    
    # Create Claude Desktop config
    $mcpConfig = @{
        mcpServers = @{
            "nano-agent" = @{
                command = $nanoAgentCmd
                args = @()
                env = @{
                    NANO_AGENT_MCP_MODE = "true"
                }
            }
        }
    } | ConvertTo-Json -Depth 4
    
    $mcpConfig | Out-File -FilePath "$claudeConfigDir\claude_desktop_config.json" -Encoding UTF8
    Write-Success "Claude Desktop configuration created"
    
    Write-Host ""
    Write-Host "Claude Desktop Setup Complete!" -ForegroundColor Green -BackgroundColor Black
    Write-Host ""
    Write-Host "To use with Claude Desktop:"
    Write-Host "1. Restart Claude Desktop"
    Write-Host "2. Look for the 🔌 icon"
    Write-Host "3. Try: 'Use nano-agent to create a hello world script'"
    Write-Host ""
}

function Show-Completion {
    Clear-Host
    Write-Host ""
    Write-Host "🎉 Installation Complete!" -ForegroundColor Green -BackgroundColor Black
    Write-Host ""
    Write-Host "Nano Agent MCP Server has been successfully installed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📍 Installation Locations:" -ForegroundColor White
    Write-Host "• Program files: $InstallDir\nano-agent"
    Write-Host "• Configuration: $ConfigDir"
    Write-Host "• Command: nano-agent"
    Write-Host ""
    Write-Host "🚀 What's Next:" -ForegroundColor White
    Write-Host ""
    Write-Host "For Claude Desktop users:"
    Write-Host "  • Restart Claude Desktop"
    Write-Host "  • Look for the 🔌 icon to access nano-agent"
    Write-Host "  • Try: 'Use nano-agent to analyze this project'"
    Write-Host ""
    Write-Host "For CLI users:"
    Write-Host "  • Run: nano-cli run 'your prompt here'"
    Write-Host "  • Example: nano-cli run 'Create a Python script'"
    Write-Host ""
    Write-Host "📝 Configure API Keys:"
    Write-Host "  Edit: $InstallDir\nano-agent\apps\nano_agent_mcp_server\.env"
    Write-Host ""
    Write-Host "Happy coding! 🤖✨" -ForegroundColor Green
    Write-Host ""
}

# Main installation flow
function Main {
    if (!$Quick) {
        $continue = Read-Host "Continue with installation? (y/N)"
        if ($continue -ne 'y' -and $continue -ne 'Y') {
            Write-Host "Installation cancelled."
            exit 0
        }
    }
    
    if (!(Test-Requirements)) {
        exit 1
    }
    
    Install-UV
    Install-NanoAgent
    Setup-Configuration
    Setup-ClaudeDesktop
    Show-Completion
}

# Handle Ctrl+C gracefully
try {
    Main
} catch {
    Write-Error "Installation interrupted: $($_.Exception.Message)"
    exit 1
}