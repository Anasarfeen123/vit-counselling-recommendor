#!/bin/bash
# run_app.sh - Switch between main app and admin dashboard

echo "╔═════════════════════════════════════════╗"
echo "║  VIT Counselling Predictor - App Switcher"
echo "╚═════════════════════════════════════════╝"
echo ""
echo "Select which app to run:"
echo "1) Main App (Student Recommendations)"
echo "2) Admin Dashboard (Data Management)"
echo ""
read -p "Enter your choice (1 or 2): " choice

case $choice in
    1)
        echo "🎓 Starting Main App..."
        streamlit run app.py
        ;;
    2)
        echo "⚙️ Starting Admin Dashboard..."
        streamlit run admin_app.py
        ;;
    *)
        echo "❌ Invalid choice. Please select 1 or 2."
        exit 1
        ;;
esac
