# README

Оригинальный [README.VTB.md](README.VTB.md)

- Наш репо: https://github.com/61whey/banking-box
- ВТБ репо: https://github.com/GalkinTech/bank-in-a-box

## TODO

[TODO](doc/TODO.md)

## Docs

- Документация ВТБ перенесена сюда:
  - [README.VTB.md](README.VTB.md)
  - [doc/vtb/](doc/vtb/)


## AGENTS.md

[AGENTS.md](AGENTS.md) - единый файл для всех coding agents. Редактируйте его.

# Local development

- Почти все значения по-умолчанию удалены, чтобы было проще траблшутить. Используйте .env файл.

Fast remove & rebuild & restart:
```shell
docker compose down; sudo rm -rf /opt/banking-box/postgresql; docker image rm -f banking-box-bank; docker compose up -d
```
