#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")"
if [ ! -d ".venv" ]; then
  python -m venv .venv
fi
. .venv/bin/activate
pip install -r requirements.txt
echo ""
echo "Website: http://127.0.0.1:5000"
echo "Default first-run admin password: ChangeMe123!"
echo "Login ke baad password badalne ka option is starter version mein nahi hai."
echo "IMPORTANT: First run se pehle ADMIN_PASSWORD set karke password choose karein."
python app.py
