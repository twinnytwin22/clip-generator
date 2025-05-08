#!/bin/zsh

echo "🧹 Cleaning old environment..."
rm -rf .venv

echo "🐍 Checking Python 3 availability..."
if ! command -v python3 &> /dev/null
then
  echo "❌ Python 3 not found. Installing via Homebrew..."
  brew install python
else
  echo "✅ Python 3 found: $(python3 --version)"
fi

echo "📦 Creating new virtual environment..."
python3 -m venv .venv

echo "⚡ Activating virtual environment..."
source .venv/bin/activate

echo "⬆️ Upgrading pip..."
pip install --upgrade pip

if [ -f requirements.txt ]; then
  echo "📥 Installing requirements..."
  pip install -r requirements.txt
else
  echo "⚠️ requirements.txt not found. Skipping install."
fi

# 🧪 Install python-dotenv for .env support
pip install python-dotenv

# ➕ Add .env example file if not present
if [ ! -f .env ]; then
  echo "🎯 Creating .env file..."
  echo "# Add your environment variables here" > .env
  echo "INPUT_DIR=./input" >> .env
fi

# 🚀 Add run script for backend
cat << 'EOF' > run-backend.sh
#!/bin/zsh
source .venv/bin/activate
echo "Running backend..."
python main.py
EOF

chmod +x run-backend.sh

echo ""
echo "✅ Setup complete!"
echo "👉 To activate the environment: source .venv/bin/activate"
echo "👉 To run the backend: ./run-backend.sh"
