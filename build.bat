@echo off
call .venv\Scripts\activate
pyinstaller --onedir --clean --noupx --windowed --noconfirm --add-data "exclusion_periods.json;." --exclude-module "test_db" --exclude-module "backup" --exclude-module "backups" --exclude-module "spreadsheets" --exclude-module "tests" --hidden-import "pandas" "eightbox.py"
echo Build complete! Your executable is in dist/eightbox/eightbox.exe 