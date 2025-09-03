# WorldAlphabets TTS Environment Variables
# Run this script before generating audio: . .\set_env.ps1

Write-Host "Setting TTS environment variables..." -ForegroundColor Green

# Google TTS
$env:GOOGLE_SA_PATH = ".googleServiceJSON.json"
Write-Host "✅ GOOGLE_SA_PATH set" -ForegroundColor Green

# Microsoft Azure TTS
$env:MICROSOFT_TOKEN = "b14f8945b0f1459f9964bdd72c42c2cc"
$env:MICROSOFT_REGION = "uksouth"
Write-Host "✅ MICROSOFT_TOKEN and MICROSOFT_REGION set" -ForegroundColor Green

# UpliftAI
$env:UPLIFTAI_KEY = "sk_api_cbf905b4b4a90faacc4f2635eb8b5d4a8f0e128560c15f3a560c2de26d5cd0b9"
Write-Host "✅ UPLIFTAI_KEY set" -ForegroundColor Green

# Optional: Add other TTS engines if you have keys
# $env:OPENAI_API_KEY = "your-openai-key"
# $env:ELEVENLABS_API_KEY = "your-elevenlabs-key"
# $env:POLLY_AWS_KEY_ID = "your-aws-key-id"
# $env:POLLY_AWS_ACCESS_KEY = "your-aws-access-key"
# $env:POLLY_REGION = "us-east-1"

Write-Host "🎵 Environment variables set! You can now run:" -ForegroundColor Cyan
Write-Host "   uv run python scripts/generate_audio.py --skip-existing" -ForegroundColor Yellow

# Verify the variables are set
Write-Host "`nVerification:" -ForegroundColor Magenta
Write-Host "GOOGLE_SA_PATH: $env:GOOGLE_SA_PATH"
Write-Host "MICROSOFT_TOKEN: $($env:MICROSOFT_TOKEN.Substring(0,8))..."
Write-Host "MICROSOFT_REGION: $env:MICROSOFT_REGION"
Write-Host "UPLIFTAI_KEY: $($env:UPLIFTAI_KEY.Substring(0,12))..."
