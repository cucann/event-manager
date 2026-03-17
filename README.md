# Event Manager App

## 📋 О проекте
Приложение для управления корпоративными событиями, развернутое в Kubernetes.

## 🛠 Технологии
- Backend: FastAPI + MongoDB
- Frontend: Streamlit
- Container: Docker
- Orchestration: Kubernetes

## 📦 Версии
- v1.0.0 - Базовая версия с CRUD
- v1.1.0 - Добавлены уведомления и таймер

## 🚀 Запуск
```bash
kubectl apply -f k8s/fullstack.yaml
kubectl port-forward deployment/frontend-deployment 8501:8501
```
EOF 
eof
