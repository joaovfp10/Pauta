"""Entidades do sistema Pauta, mapeadas com SQLAlchemy."""
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


def agora() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

PERFIS = {"gestor": "Gestor", "social_media": "Social media"}

FORMATOS = {
    "feed": "Post de feed",
    "carrossel": "Carrossel",
    "reels": "Reels",
    "stories": "Stories",
}

STATUS = {
    "rascunho": "Rascunho",
    "em_revisao": "Em revisão",
    "ajustes": "Ajustes solicitados",
    "aprovado": "Aprovado",
    "publicado": "Publicado",
}


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    perfil = db.Column(db.String(20), nullable=False, default="social_media")
    criado_em = db.Column(db.DateTime, default=agora, nullable=False)

    conteudos = db.relationship("Conteudo", back_populates="responsavel")
    revisoes = db.relationship("Revisao", back_populates="revisor")

    def definir_senha(self, senha: str) -> None:
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha: str) -> bool:
        return check_password_hash(self.senha_hash, senha)

    @property
    def is_gestor(self) -> bool:
        return self.perfil == "gestor"


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False)
    segmento = db.Column(db.String(80))
    instagram = db.Column(db.String(60))
    email_contato = db.Column(db.String(120))
    telefone = db.Column(db.String(20))
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    criado_em = db.Column(db.DateTime, default=agora, nullable=False)

    conteudos = db.relationship("Conteudo", back_populates="cliente")

    def pode_ser_excluido(self) -> bool:
        """Regra de negócio: cliente com conteúdo vinculado só pode ser inativado."""
        return len(self.conteudos) == 0


class Conteudo(db.Model):
    __tablename__ = "conteudos"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    responsavel_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    titulo = db.Column(db.String(150), nullable=False)
    formato = db.Column(db.String(20), nullable=False, default="feed")
    legenda = db.Column(db.Text)
    data_publicacao = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="rascunho")
    criado_em = db.Column(db.DateTime, default=agora, nullable=False)
    atualizado_em = db.Column(
        db.DateTime, default=agora, onupdate=agora, nullable=False
    )

    cliente = db.relationship("Cliente", back_populates="conteudos")
    responsavel = db.relationship("Usuario", back_populates="conteudos")
    revisoes = db.relationship(
        "Revisao",
        back_populates="conteudo",
        cascade="all, delete-orphan",
        order_by="Revisao.criado_em.desc()",
    )

    def pode_ser_editado(self) -> bool:
        return self.status in ("rascunho", "ajustes")

    def enviar_para_revisao(self) -> None:
        if not self.pode_ser_editado():
            raise ValueError("Só é possível enviar rascunhos ou conteúdos com ajustes.")
        self.status = "em_revisao"


class Revisao(db.Model):
    __tablename__ = "revisoes"

    id = db.Column(db.Integer, primary_key=True)
    conteudo_id = db.Column(db.Integer, db.ForeignKey("conteudos.id"), nullable=False)
    revisor_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    decisao = db.Column(db.String(20), nullable=False)  # aprovado | ajustes
    comentario = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=agora, nullable=False)

    conteudo = db.relationship("Conteudo", back_populates="revisoes")
    revisor = db.relationship("Usuario", back_populates="revisoes")
