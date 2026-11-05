"""Dados de exemplo para demonstração do sistema."""
from datetime import date, timedelta

from .models import Cliente, Conteudo, Revisao, Usuario, db


def popular_banco() -> None:
    if Usuario.query.first():
        return

    gestor = Usuario(nome="Ana Gestora", email="gestor@pauta.dev", perfil="gestor")
    gestor.definir_senha("123456")
    social = Usuario(nome="Bruno Social", email="social@pauta.dev", perfil="social_media")
    social.definir_senha("123456")

    clientes = [
        Cliente(nome="Café da Serra", segmento="Alimentação", instagram="cafedaserra"),
        Cliente(nome="Agro Campo Verde", segmento="Agronegócio", instagram="campoverde.agro"),
        Cliente(nome="Studio Fit", segmento="Saúde e bem-estar", instagram="studiofit"),
    ]
    db.session.add_all([gestor, social, *clientes])
    db.session.flush()

    hoje = date.today()
    exemplos = [
        ("Lançamento do blend de inverno", "carrossel", 2, "aprovado", clientes[0]),
        ("Bastidores da torra", "reels", 4, "em_revisao", clientes[0]),
        ("Dia de campo: manejo de solo", "feed", 1, "rascunho", clientes[1]),
        ("Depoimento de produtor", "reels", 6, "ajustes", clientes[1]),
        ("Treino de 15 minutos", "stories", 3, "publicado", clientes[2]),
        ("Mitos sobre alimentação", "carrossel", 9, "rascunho", clientes[2]),
    ]
    for titulo, formato, dias, status, cliente in exemplos:
        conteudo = Conteudo(
            titulo=titulo,
            formato=formato,
            data_publicacao=hoje + timedelta(days=dias),
            status=status,
            cliente=cliente,
            responsavel=social,
            legenda=f"Legenda de exemplo para {titulo.lower()}.",
        )
        db.session.add(conteudo)
        if status in ("aprovado", "ajustes", "publicado"):
            db.session.add(
                Revisao(
                    conteudo=conteudo,
                    revisor=gestor,
                    decisao="ajustes" if status == "ajustes" else "aprovado",
                    comentario="Trocar a foto de capa." if status == "ajustes" else "",
                )
            )
    db.session.commit()
