#!/bin/bash

# Получаем текущую дату в формате ГГГГ-ММ-ДД
current_date=$(date +%F)

# Указываем путь к директории логов
log_directory="./logs"

# Создаем директорию, если она не существует
mkdir -p $log_directory

# Формируем имя файла лога
log_file="${log_directory}/project_container_${current_date}.log"

# Запускаем docker-compose и логируем вывод
docker-compose --env-file .env.prod -f docker-compose.prod.yml up --build | tee -a "$log_file"
