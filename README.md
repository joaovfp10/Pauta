# Pauta

Sistema web de gestão de clientes e conteúdo para agências de marketing digital.
Projeto desenvolvido para as disciplinas Projeto de Desenvolvimento de Software I e II do curso de Engenharia de Software da UniFil.

**Autor:** João Victor Ferreira Pinto (trabalho individual)

## O que o sistema faz

* Autenticação de usuários com dois perfis: Gestor e Social media
* CRUD de clientes da agência (cliente com conteúdo vinculado é inativado em vez de excluído)
* CRUD de conteúdos (título, cliente, formato, data de publicação e legenda)
* Fluxo de revisão: o social media envia o conteúdo, o gestor aprova ou solicita ajustes com comentário
* Calendário editorial mensal com filtro por cliente

## Stack

* Python 3.10 ou superior
* Flask 3 (framework web)
* Flask-SQLAlchemy (ORM)
* SQLite (banco de dados relacional)
* Jinja2, HTML e CSS (interface)
* Pytest (testes automatizados)

## Como rodar

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
flask --app pauta popular      # cria o banco com dados de exemplo
flask --app pauta run          # abre em http://127.0.0.1:5000
```

Usuários de exemplo (senha `123456`):

| Perfil | E-mail |
|---|---|
| Gestor | gestor@pauta.dev |
| Social media | social@pauta.dev |

Para cadastrar outro usuário: `flask --app pauta criar-usuario`

## Testes

```bash
python -m pytest
```

## Estrutura

```
pauta/
  __init__.py      rotas e regras de cada caso de uso
  models.py        entidades Usuario, Cliente, Conteudo e Revisao
  seed.py          dados de exemplo
  templates/       telas em Jinja2
  static/          estilo
tests/             testes dos cinco casos de uso
docs/              documentação em PDF, diagramas e telas
```

## Documentação

A documentação completa (requisitos, diagramas UML e DER) está em `docs/Documentacao_Pauta.pdf`.
