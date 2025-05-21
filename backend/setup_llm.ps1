# PowerShell script to set up and test the LLM fallback parser

# Install required packages
Write-Host "Installing required packages..." -ForegroundColor Green
pip install python-dotenv requests

# Set up and validate the environment
Write-Host "`nSetting up and validating the environment..." -ForegroundColor Green
python check_env.py

# If the environment is set up correctly, test the LLM parser
if (Test-Path .env) {
    $env_content = Get-Content .env -Raw
    if ($env_content -match "OPENAI_API_KEY=([^`r`n]+)" -and $matches[1] -ne "your_openai_api_key_here") {
        Write-Host "`nTesting the LLM fallback parser..." -ForegroundColor Green
        python test_llm_directly.py
    } else {
        Write-Host "`nOpenAI API key not properly set in .env file." -ForegroundColor Red
        Write-Host "Please run 'python check_env.py' and enter a valid API key." -ForegroundColor Yellow
    }
} else {
    Write-Host "`n.env file not found." -ForegroundColor Red
    Write-Host "Please run 'python check_env.py' to create it." -ForegroundColor Yellow
}

Write-Host "`nSetup complete. Use the LLM fallback parser by uploading a document to the application." -ForegroundColor Green 