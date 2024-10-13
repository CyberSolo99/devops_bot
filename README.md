# DevOps Bot Project on Ansible

## Описание
Этот проект предназначен для автоматизации инфраструктуры и управления ею с использованием Ansible. 

## Проект выполняется с помощью ansible
Перед запуском редактируйте inventory.yml под свои нужды

Для запуска:
```bash
ansible-playbook playbook_bot.yml
```
### Требования
На машинах установлено все для ansible, созданы пользователи ansible и добавлены привилегии прав администратора без пароля (sudo visudo)

Добавить пользователей на ваших машинах в группу ansible


