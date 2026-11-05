"""Testes automatizados dos cinco casos de uso do Pauta."""
from datetime import date

import pytest

from pauta import create_app
from pauta.models import Cliente, Conteudo, Revisao, Usuario, db


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "TESTING_SEM_CSRF": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )
    with app.app_context():
        gestor = Usuario(nome="Gestora", email="g@t.dev", perfil="gestor")
        gestor.definir_senha("senha")
        social = Usuario(nome="Social", email="s@t.dev", perfil="social_media")
        social.definir_senha("senha")
        db.session.add_all([gestor, social, Cliente(nome="Cliente A")])
        db.session.commit()
    yield app


def entrar(client, email):
    return client.post("/login", data={"email": email, "senha": "senha"})


# UC01
def test_login_valido_e_invalido(app):
    c = app.test_client()
    assert c.get("/").status_code == 302
    r = c.post("/login", data={"email": "g@t.dev", "senha": "errada"})
    assert "inválidos" in r.get_data(as_text=True)
    assert entrar(c, "g@t.dev").status_code == 302
    assert c.get("/").status_code == 200


# UC02
def test_crud_cliente(app):
    c = app.test_client()
    entrar(c, "g@t.dev")
    c.post("/clientes/novo", data={"nome": "Novo", "instagram": "@novo", "ativo": "on"})
    with app.app_context():
        cli = Cliente.query.filter_by(nome="Novo").one()
        assert cli.instagram == "novo"
        cid = cli.id
    c.post(f"/clientes/{cid}/editar", data={"nome": "Renomeado", "ativo": "on"})
    assert "Renomeado" in c.get("/clientes").get_data(as_text=True)
    c.post(f"/clientes/{cid}/excluir")
    with app.app_context():
        assert db.session.get(Cliente, cid) is None


def test_social_media_nao_gerencia_clientes(app):
    c = app.test_client()
    entrar(c, "s@t.dev")
    assert c.get("/clientes/novo").status_code == 403


def test_cliente_com_conteudo_e_inativado(app):
    c = app.test_client()
    entrar(c, "g@t.dev")
    with app.app_context():
        cli = Cliente.query.first()
        db.session.add(
            Conteudo(titulo="X", cliente=cli, responsavel_id=1, data_publicacao=date.today())
        )
        db.session.commit()
        cid = cli.id
    c.post(f"/clientes/{cid}/excluir")
    with app.app_context():
        assert db.session.get(Cliente, cid).ativo is False


# UC03
def test_crud_conteudo(app):
    c = app.test_client()
    entrar(c, "s@t.dev")
    dados = {"titulo": "Post 1", "cliente_id": 1, "formato": "reels", "data_publicacao": "2026-11-20"}
    c.post("/conteudos/novo", data=dados)
    with app.app_context():
        cont = Conteudo.query.one()
        assert cont.status == "rascunho"
    c.post("/conteudos/1/editar", data={**dados, "titulo": "Post editado"})
    assert "Post editado" in c.get("/conteudos").get_data(as_text=True)
    c.post("/conteudos/1/excluir")
    with app.app_context():
        assert Conteudo.query.count() == 0


def test_conteudo_sem_titulo_e_rejeitado(app):
    c = app.test_client()
    entrar(c, "s@t.dev")
    c.post("/conteudos/novo", data={"titulo": "", "cliente_id": 1, "formato": "feed", "data_publicacao": "2026-11-20"})
    with app.app_context():
        assert Conteudo.query.count() == 0


# UC04
def test_fluxo_de_revisao(app):
    s, g = app.test_client(), app.test_client()
    entrar(s, "s@t.dev")
    entrar(g, "g@t.dev")
    s.post("/conteudos/novo", data={"titulo": "Post", "cliente_id": 1, "formato": "feed", "data_publicacao": "2026-11-20"})
    s.post("/conteudos/1/enviar")
    assert s.post("/conteudos/1/revisar", data={"decisao": "aprovado"}).status_code == 403
    g.post("/conteudos/1/revisar", data={"decisao": "ajustes", "comentario": ""})
    with app.app_context():
        assert db.session.get(Conteudo, 1).status == "em_revisao"
    g.post("/conteudos/1/revisar", data={"decisao": "ajustes", "comentario": "Trocar foto"})
    s.post("/conteudos/1/enviar")
    g.post("/conteudos/1/revisar", data={"decisao": "aprovado"})
    s.post("/conteudos/1/publicar")
    with app.app_context():
        assert db.session.get(Conteudo, 1).status == "publicado"
        assert Revisao.query.count() == 2


# UC05
def test_calendario(app):
    c = app.test_client()
    entrar(c, "s@t.dev")
    c.post("/conteudos/novo", data={"titulo": "Natal", "cliente_id": 1, "formato": "feed", "data_publicacao": "2026-12-24"})
    html = c.get("/calendario?ano=2026&mes=12").get_data(as_text=True)
    assert "Dezembro de 2026" in html and "Natal" in html
    assert "Natal" not in c.get("/calendario?ano=2026&mes=11").get_data(as_text=True)
