#!/bin/sh

# Запускаем MinIO в фоновом режиме
minio server /data --console-address :9001 &

# Ждем запуска MinIO
sleep 3

# Настройка mc
mc alias set minio http://localhost:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD}

# Выполнение обновления MinIO
#mc admin update minio

wait