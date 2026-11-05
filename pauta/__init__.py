"""Pauta: sistema de gestão de clientes e conteúdo para agências de marketing."""
import calendar
import os
import secrets
from datetime import date
from functools import wraps

import click
from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from .models import FORMATOS, PERFIS, STATUS, Cliente, Conteudo, Revisao, Usuario, db

MESES = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)
    app.config.update(
        SECRET_KEY=os.environ.get("PAUTA_SECRET_KEY", "troque-esta-chave-em-producao"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", "sqlite:///" + os.path.join(app.instance_path, "pauta.db")
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if config:
        app.config.update(config)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    registrar_auxiliares(app)
    registrar_rotas(app)
    registrar_comandos(app)
    return app


# ---------------------------------------------------------------- auxiliares
def registrar_auxiliares(app: Flask) -> None:
    @app.before_request
    def carregar_usuario():
        uid = session.get("usuario_id")
        g.usuario = db.session.get(Usuario, uid) if uid else None

    @app.before_request
    def validar_csrf():
        if request.method == "POST" and not app.config.get("TESTING_SEM_CSRF"):
            token = session.get("csrf_token")
            if not token or token != request.form.get("csrf_token"):
                abort(400, "Token de segurança inválido. Recarregue a página.")

    @app.context_processor
    def injetar():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(16)
        return {
            "usuario": g.get("usuario"),
            "csrf_token": session["csrf_token"],
            "FORMATOS": FORMATOS,
            "STATUS": STATUS,
            "PERFIS": PERFIS,
        }


def login_obrigatorio(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if g.usuario is None:
            return redirect(url_for("login", proximo=request.path))
        return view(*args, **kwargs)

    return wrapper


def somente_gestor(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if g.usuario is None:
            return redirect(url_for("login"))
        if not g.usuario.is_gestor:
            abort(403)
        return view(*args, **kwargs)

    return wrapper


def ler_data(texto: str) -> date | None:
    try:
        return date.fromisoformat(texto)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- rotas
def registrar_rotas(app: Flask) -> None:
    # UC01 Autenticar no sistema
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            senha = request.form.get("senha", "")
            usuario = Usuario.query.filter_by(email=email).first()
            if usuario and usuario.verificar_senha(senha):
                session.clear()
                session["usuario_id"] = usuario.id
                destino = request.args.get("proximo") or url_for("painel")
                if not destino.startswith("/"):
                    destino = url_for("painel")
                return redirect(destino)
            flash("E-mail ou senha inválidos.", "erro")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/")
    @login_obrigatorio
    def painel():
        contagem = {
            chave: Conteudo.query.filter_by(status=chave).count() for chave in STATUS
        }
        proximos = (
            Conteudo.query.filter(Conteudo.data_publicacao >= date.today())
            .order_by(Conteudo.data_publicacao)
            .limit(5)
            .all()
        )
        return render_template(
            "painel.html",
            contagem=contagem,
            proximos=proximos,
            total_clientes=Cliente.query.filter_by(ativo=True).count(),
        )

    # UC02 Manter clientes
    @app.route("/clientes")
    @login_obrigatorio
    def clientes_listar():
        busca = request.args.get("q", "").strip()
        consulta = Cliente.query
        if busca:
            consulta = consulta.filter(Cliente.nome.ilike(f"%{busca}%"))
        clientes = consulta.order_by(Cliente.ativo.desc(), Cliente.nome).all()
        return render_template("clientes/lista.html", clientes=clientes, busca=busca)

    @app.route("/clientes/novo", methods=["GET", "POST"])
    @somente_gestor
    def clientes_criar():
        cliente = Cliente()
        if request.method == "POST":
            if preencher_cliente(cliente, request.form):
                db.session.add(cliente)
                db.session.commit()
                flash("Cliente cadastrado.", "ok")
                return redirect(url_for("clientes_listar"))
        return render_template("clientes/form.html", cliente=cliente)

    @app.route("/clientes/<int:cliente_id>/editar", methods=["GET", "POST"])
    @somente_gestor
    def clientes_editar(cliente_id):
        cliente = db.get_or_404(Cliente, cliente_id)
        if request.method == "POST":
            if preencher_cliente(cliente, request.form):
                db.session.commit()
                flash("Cliente atualizado.", "ok")
                return redirect(url_for("clientes_listar"))
        return render_template("clientes/form.html", cliente=cliente)

    @app.route("/clientes/<int:cliente_id>/excluir", methods=["POST"])
    @somente_gestor
    def clientes_excluir(cliente_id):
        cliente = db.get_or_404(Cliente, cliente_id)
        if cliente.pode_ser_excluido():
            db.session.delete(cliente)
            flash("Cliente excluído.", "ok")
        else:
            cliente.ativo = False
            flash("O cliente tem conteúdos vinculados e foi inativado.", "aviso")
        db.session.commit()
        return redirect(url_for("clientes_listar"))

    # UC03 Manter conteúdos
    @app.route("/conteudos")
    @login_obrigatorio
    def conteudos_listar():
        consulta = Conteudo.query
        cliente_id = request.args.get("cliente", type=int)
        status = request.args.get("status")
        if cliente_id:
            consulta = consulta.filter_by(cliente_id=cliente_id)
        if status in STATUS:
            consulta = consulta.filter_by(status=status)
        conteudos = consulta.order_by(Conteudo.data_publicacao).all()
        return render_template(
            "conteudos/lista.html",
            conteudos=conteudos,
            clientes=Cliente.query.order_by(Cliente.nome).all(),
            filtro_cliente=cliente_id,
            filtro_status=status,
        )

    @app.route("/conteudos/novo", methods=["GET", "POST"])
    @login_obrigatorio
    def conteudos_criar():
        conteudo = Conteudo(responsavel_id=g.usuario.id)
        if request.method == "POST":
            if preencher_conteudo(conteudo, request.form):
                db.session.add(conteudo)
                db.session.commit()
                flash("Conteúdo criado como rascunho.", "ok")
                return redirect(url_for("conteudos_detalhe", conteudo_id=conteudo.id))
        return render_template(
            "conteudos/form.html", conteudo=conteudo, clientes=clientes_ativos()
        )

    @app.route("/conteudos/<int:conteudo_id>")
    @login_obrigatorio
    def conteudos_detalhe(conteudo_id):
        conteudo = db.get_or_404(Conteudo, conteudo_id)
        return render_template("conteudos/detalhe.html", conteudo=conteudo)

    @app.route("/conteudos/<int:conteudo_id>/editar", methods=["GET", "POST"])
    @login_obrigatorio
    def conteudos_editar(conteudo_id):
        conteudo = db.get_or_404(Conteudo, conteudo_id)
        if not conteudo.pode_ser_editado():
            flash("Só rascunhos ou conteúdos com ajustes podem ser editados.", "aviso")
            return redirect(url_for("conteudos_detalhe", conteudo_id=conteudo.id))
        if request.method == "POST":
            if preencher_conteudo(conteudo, request.form):
                db.session.commit()
                flash("Conteúdo atualizado.", "ok")
                return redirect(url_for("conteudos_detalhe", conteudo_id=conteudo.id))
        return render_template(
            "conteudos/form.html", conteudo=conteudo, clientes=clientes_ativos()
        )

    @app.route("/conteudos/<int:conteudo_id>/excluir", methods=["POST"])
    @login_obrigatorio
    def conteudos_excluir(conteudo_id):
        conteudo = db.get_or_404(Conteudo, conteudo_id)
        if conteudo.status == "publicado":
            flash("Conteúdos publicados não podem ser excluídos.", "aviso")
            return redirect(url_for("conteudos_detalhe", conteudo_id=conteudo.id))
        db.session.delete(conteudo)
        db.session.commit()
        flash("Conteúdo excluído.", "ok")
        return redirect(url_for("conteudos_listar"))

    @app.route("/conteudos/<int:conteudo_id>/enviar", methods=["POST"])
    @login_obrigatorio
    def conteudos_enviar(conteudo_id):
        conteudo = db.get_or_404(Conteudo, conteudo_id)
        try:
            conteudo.enviar_para_revisao()
            db.session.commit()
            flash("Conteúdo enviado para revisão.", "ok")
        except ValueError as erro:
            flash(str(erro), "aviso")
        return redirect(url_for("conteudos_detalhe", conteudo_id=conteudo.id))

    # UC04 Revisar conteúdo
    @app.route("/conteudos/<int:conteudo_id>/revisar", methods=["POST"])
    @somente_gestor
    def conteudos_revisar(conteudo_id):
        conteudo = db.get_or_404(Conteudo, conteudo_id)
        decisao = request.form.get("decisao")
        comentario = request.form.get("comentario", "").strip()
        if conteudo.status != "em_revisao":
            flash("Este conteúdo não está aguardando revisão.", "aviso")
        elif decisao not in ("aprovado", "ajustes"):
            flash("Escolha aprovar ou solicitar ajustes.", "erro")
        elif decisao == "ajustes" and not comentario:
            flash("Descreva os ajustes que precisam ser feitos.", "erro")
        else:
            db.session.add(
                Revisao(
                    conteudo=conteudo,
                    revisor_id=g.usuario.id,
                    decisao=decisao,
                    comentario=comentario,
                )
            )
            conteudo.status = decisao
            db.session.commit()
            flash("Revisão registrada.", "ok")
        return redirect(url_for("conteudos_detalhe", conteudo_id=conteudo.id))

    @app.route("/conteudos/<int:conteudo_id>/publicar", methods=["POST"])
    @login_obrigatorio
    def conteudos_publicar(conteudo_id):
        conteudo = db.get_or_404(Conteudo, conteudo_id)
        if conteudo.status != "aprovado":
            flash("Só conteúdos aprovados podem ser marcados como publicados.", "aviso")
        else:
            conteudo.status = "publicado"
            db.session.commit()
            flash("Conteúdo marcado como publicado.", "ok")
        return redirect(url_for("conteudos_detalhe", conteudo_id=conteudo.id))

    # UC05 Consultar calendário editorial
    @app.route("/calendario")
    @login_obrigatorio
    def calendario_ver():
        hoje = date.today()
        ano = request.args.get("ano", hoje.year, type=int)
        mes = request.args.get("mes", hoje.month, type=int)
        if not 1 <= mes <= 12:
            mes = hoje.month
        cliente_id = request.args.get("cliente", type=int)
        inicio = date(ano, mes, 1)
        fim = date(ano, mes, calendar.monthrange(ano, mes)[1])
        consulta = Conteudo.query.filter(Conteudo.data_publicacao.between(inicio, fim))
        if cliente_id:
            consulta = consulta.filter_by(cliente_id=cliente_id)
        por_dia: dict[int, list[Conteudo]] = {}
        for item in consulta.order_by(Conteudo.data_publicacao).all():
            por_dia.setdefault(item.data_publicacao.day, []).append(item)
        anterior = (ano, mes - 1) if mes > 1 else (ano - 1, 12)
        seguinte = (ano, mes + 1) if mes < 12 else (ano + 1, 1)
        return render_template(
            "calendario.html",
            semanas=calendar.Calendar(firstweekday=6).monthdayscalendar(ano, mes),
            por_dia=por_dia,
            titulo=f"{MESES[mes]} de {ano}",
            anterior=anterior,
            seguinte=seguinte,
            clientes=Cliente.query.order_by(Cliente.nome).all(),
            filtro_cliente=cliente_id,
            hoje=hoje,
            ano=ano,
            mes=mes,
        )


def clientes_ativos():
    return Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()


def preencher_cliente(cliente: Cliente, form) -> bool:
    nome = form.get("nome", "").strip()
    if not nome:
        flash("O nome do cliente é obrigatório.", "erro")
        return False
    cliente.nome = nome
    cliente.segmento = form.get("segmento", "").strip() or None
    instagram = form.get("instagram", "").strip().lstrip("@")
    cliente.instagram = instagram or None
    cliente.email_contato = form.get("email_contato", "").strip() or None
    cliente.telefone = form.get("telefone", "").strip() or None
    cliente.ativo = form.get("ativo") == "on"
    return True


def preencher_conteudo(conteudo: Conteudo, form) -> bool:
    titulo = form.get("titulo", "").strip()
    cliente_id = form.get("cliente_id", type=int)
    data_pub = ler_data(form.get("data_publicacao"))
    formato = form.get("formato")
    erros = []
    if not titulo:
        erros.append("O título é obrigatório.")
    if not cliente_id or db.session.get(Cliente, cliente_id) is None:
        erros.append("Selecione um cliente.")
    if data_pub is None:
        erros.append("Informe uma data de publicação válida.")
    if formato not in FORMATOS:
        erros.append("Escolha um formato válido.")
    for erro in erros:
        flash(erro, "erro")
    if erros:
        return False
    conteudo.titulo = titulo
    conteudo.cliente_id = cliente_id
    conteudo.data_publicacao = data_pub
    conteudo.formato = formato
    conteudo.legenda = form.get("legenda", "").strip() or None
    return True


# ---------------------------------------------------------------- comandos
def registrar_comandos(app: Flask) -> None:
    @app.cli.command("criar-usuario")
    @click.option("--nome", prompt=True)
    @click.option("--email", prompt=True)
    @click.option("--perfil", type=click.Choice(list(PERFIS)), default="social_media")
    @click.password_option("--senha")
    def criar_usuario(nome, email, perfil, senha):
        """Cadastra um usuário pelo terminal."""
        usuario = Usuario(nome=nome, email=email.lower(), perfil=perfil)
        usuario.definir_senha(senha)
        db.session.add(usuario)
        db.session.commit()
        click.echo(f"Usuário {email} criado com perfil {perfil}.")

    @app.cli.command("popular")
    def popular():
        """Cria dados de exemplo para demonstração."""
        from .seed import popular_banco

        popular_banco()
        click.echo("Banco populado. Logins: gestor@pauta.dev e social@pauta.dev, senha 123456")
