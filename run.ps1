# Move to project root
Set-Location $PSScriptRoot

# Create venv if not exists
if (!(Test-Path ".venv")) {
    python -m venv .venv
}

# Activate venv
.\.venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Run Streamlit
python -m streamlit run app.py
