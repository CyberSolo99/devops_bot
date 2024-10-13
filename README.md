# DevOps Bot Project on Docker

## Требования
1. Установите Docker и Docker Compose как в методических указаниях в занятии 3
2. Клонируйте репозиторий:
```bash
git clone https://github.com/CyberSolo99/devops_bot.git
```
3. Отредактируйте файл .env

## Запуск 
В корневой директории проекта:
```bash
docker compose build
```
После того как процесс закончится
```bash
docker network create my_network
```
И запуск контейнеров
```bash
docker compose up
```

Для проекта использовалась Ubuntu 22.04 server
