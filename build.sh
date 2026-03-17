#!/bin/bash

echo "🚀 Запуск CI процесса..."

# Получаем версию из git (хэш коммита)
VERSION=$(git rev-parse --short HEAD)
echo "📌 Версия: ${VERSION}"

# Собираем бэкенд
echo "🔨 Сборка бэкенда..."
cd src/backend
docker build -t event-backend:${VERSION} .
docker tag event-backend:${VERSION} event-backend:latest

# Собираем фронтенд
echo "🔨 Сборка фронтенда..."
cd ../frontend
docker build -t event-frontend:${VERSION} .
docker tag event-frontend:${VERSION} event-frontend:latest

cd ../..

echo "✅ CI завершен! Образы собраны:"
docker images | grep event-
