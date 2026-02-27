@echo off
cd /d "%~dp0"
echo.
echo   Souvenir Petit Bellevue
echo   =======================
echo.
echo   Leggi l'indirizzo "Local URL" qui sotto
echo   e copialo nella barra di Chrome.
echo.
echo   Non chiudere questa finestra!
echo.
python -m streamlit run app.py --server.headless true
pause
