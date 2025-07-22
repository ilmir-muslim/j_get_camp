#!/bin/bash

# Рабочая директория — остаётся в app/
backups_dir="backups"
mkdir -p "$backups_dir"  # создать, если не существует

# === Корректное определение следующего номера бэкапа ===
next_backup_number=$(
  find "$backups_dir" -maxdepth 1 -type f -name "backup_*.txt" \
  | sed -E 's/.*backup_([0-9]+)\.txt/\1/' \
  | sed 's/^0*//' | sort -n | tail -1
)
if [[ -z "$next_backup_number" ]]; then
  next_backup_number=1
else
  next_backup_number=$((next_backup_number + 1))
fi

# Имя нового файла
backup_file=$(printf "%s/backup_%03d.txt" "$backups_dir" "$next_backup_number")
> "$backup_file"  # очистка/создание

EXCLUDED_PATTERNS=(
  "/__pycache__/"
  "/.pytest_cache/"
  "save_all_files.sh"
  "restore_backup.sh"
  "./backups/"
  "venv/"
  "db.sqlite3"
  "./db.sqlite3"
  "./patches/"
  "./media/"
)

is_excluded() {
  local path="$1"
  for pattern in "${EXCLUDED_PATTERNS[@]}"; do
    if [[ "$path" == *"$pattern"* ]]; then
      return 0
    fi
  done
  return 1
}

find . -type f -print0 | while IFS= read -r -d '' file; do
  if ! is_excluded "$file"; then
    echo "===== $file =====" >> "$backup_file"
    cat "$file" >> "$backup_file"
    echo -e "\n" >> "$backup_file"
  fi
done

echo "===== Структура проекта (tree из ../) =====" >> "$backup_file"
if command -v tree >/dev/null 2>&1; then
  tree -I "venv|__pycache__|node_modules|project_structure.txt|backups" >> "$backup_file" 2>/dev/null
else
  echo "[!] Утилита 'tree' не установлена, пропущено." >> "$backup_file"
fi

if command -v xclip >/dev/null 2>&1; then
  xclip -selection clipboard < "$backup_file"
  echo "📋 Содержимое бэкапа скопировано в буфер"
else
  echo "⚠️ Утилита 'xclip' не найдена, копирование в буфер пропущено"
fi

echo "✅ Сохранено как '$backup_file'"
