"""Gera docs/Documentacao_Pauta.pdf seguindo a ABNT (NBR 14724, 6023, 6024, 6027, 6028 e 10520)."""
import os

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate, PageBreak,
    PageTemplate, Paragraph, Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

AQUI = os.path.dirname(os.path.abspath(__file__))
DIAG = os.path.join(AQUI, "diagramas")
TELAS = os.path.join(AQUI, "telas")
CAPA = os.path.join(AQUI, "capa")
SAIDA = os.path.join(AQUI, "Documentacao_Pauta.pdf")

# Dados de identificação (ajuste aqui e rode o script de novo)
INSTITUICAO = "CENTRO UNIVERSITÁRIO FILADÉLFIA"
CURSO = ""  # ex.: "CURSO DE ENGENHARIA DE SOFTWARE"
AUTOR = "JOÃO VICTOR FERREIRA PINTO"
TITULO = "PAUTA"
SUBTITULO = "sistema de gestão de clientes e conteúdo para agências de marketing digital"
PROFESSOR = "Prof. Fernando Nakagawa"
CIDADE, ANO = "LONDRINA", "2026"

F = "/usr/share/fonts/truetype/liberation/"
pdfmetrics.registerFont(TTFont("Arial", F + "LiberationSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Arial-B", F + "LiberationSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Arial-I", F + "LiberationSans-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Arial-BI", F + "LiberationSans-BoldItalic.ttf"))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-B", italic="Arial-I", boldItalic="Arial-BI")

# Espaçamento 1,5 (12 pt x 1,5 = 18) no texto; simples nas legendas, quadros e referências
corpo = ParagraphStyle("corpo", fontName="Arial", fontSize=12, leading=18, alignment=TA_JUSTIFY,
                       firstLineIndent=1.25 * cm, spaceAfter=0)
alinea = ParagraphStyle("alinea", parent=corpo, firstLineIndent=0, leftIndent=1.25 * cm + 0.6 * cm,
                        bulletIndent=1.25 * cm, bulletFontName="Arial", bulletFontSize=12)
h1 = ParagraphStyle("h1", fontName="Arial-B", fontSize=12, leading=18, alignment=TA_LEFT, spaceAfter=18, keepWithNext=1)
h2 = ParagraphStyle("h2", fontName="Arial", fontSize=12, leading=18, alignment=TA_LEFT, spaceBefore=18, spaceAfter=18, keepWithNext=1)
h3 = ParagraphStyle("h3", fontName="Arial-B", fontSize=12, leading=18, alignment=TA_LEFT, spaceBefore=18, spaceAfter=18, keepWithNext=1)
sem_ind = ParagraphStyle("sem_ind", fontName="Arial-B", fontSize=12, leading=18, alignment=TA_CENTER, spaceAfter=18)
centro = ParagraphStyle("centro", fontName="Arial-B", fontSize=12, leading=18, alignment=TA_CENTER)
centro_n = ParagraphStyle("centro_n", parent=centro, fontName="Arial", leading=14)
natureza = ParagraphStyle("natureza", fontName="Arial", fontSize=12, leading=14, alignment=TA_JUSTIFY,
                          leftIndent=8 * cm)
resumo = ParagraphStyle("resumo", fontName="Arial", fontSize=12, leading=18, alignment=TA_JUSTIFY)
legenda = ParagraphStyle("legenda", fontName="Arial", fontSize=10, leading=12, alignment=TA_CENTER, spaceBefore=12)
fonte = ParagraphStyle("fonte", fontName="Arial", fontSize=10, leading=12, alignment=TA_CENTER, spaceBefore=3, spaceAfter=12)
cel = ParagraphStyle("cel", fontName="Arial", fontSize=10, leading=12)
cel_b = ParagraphStyle("cel_b", parent=cel, fontName="Arial-B", alignment=TA_CENTER)
ref = ParagraphStyle("ref", fontName="Arial", fontSize=12, leading=14, alignment=TA_LEFT, spaceAfter=14)

LARG = A4[0] - 3 * cm - 2 * cm
LARG_L = landscape(A4)[0] - 5 * cm


class Lista(TableOfContents):
    """Sumário, lista de ilustrações ou lista de quadros."""

    def __init__(self, tipo, estilos):
        super().__init__()
        self.tipo = tipo
        self.levelStyles = estilos
        self.dotsMinLevel = 0

    def notify(self, kind, stuff):
        if kind == self.tipo:
            self.addEntry(*stuff)


class Documento(BaseDocTemplate):
    def __init__(self, arquivo):
        super().__init__(arquivo, pagesize=A4, leftMargin=3 * cm, rightMargin=2 * cm,
                         topMargin=3 * cm, bottomMargin=2 * cm,
                         title=f"{TITULO}: {SUBTITULO}", author=AUTOR.title())
        quadro = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="q",
                       leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        L = landscape(A4)
        quadro_l = Frame(3 * cm, 2 * cm, L[0] - 5 * cm, L[1] - 5 * cm, id="ql",
                         leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([
            PageTemplate(id="capa", frames=[quadro], onPage=self.desenhar_capa),
            PageTemplate(id="pre", frames=[quadro]),
            PageTemplate(id="texto", frames=[quadro], onPage=self.numero),
            PageTemplate(id="deitada", frames=[quadro_l], onPage=self.numero_l, pagesize=L),
        ])

    def desenhar_capa(self, canvas, doc):
        """Capa no modelo da UniFil: logo, faixas laranja, título ao centro, cidade e ano embaixo."""
        H = A4[1]
        canvas.drawImage(os.path.join(CAPA, "logo_unifil.png"), 158.9, H - 147.0,
                         width=277.5, height=73.5, mask="auto")
        for topo in (155.1, 690.8):
            canvas.drawImage(os.path.join(CAPA, "barra.png"), 90.8, H - topo - 9,
                             width=445.4, height=9, mask="auto")
        meio = (90.8 + 536.2) / 2
        canvas.setFont("Arial", 12)
        canvas.drawCentredString(meio, H - 716, CIDADE.title())
        canvas.drawCentredString(meio, H - 730, ANO)

    # NBR 14724: folhas contadas a partir da folha de rosto (a capa não conta);
    # o número aparece a partir da primeira folha da parte textual, no canto superior direito.
    def num(self):
        return self.page - 1

    def numero(self, canvas, doc):
        canvas.setFont("Arial", 10)
        canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 2 * cm, str(self.num()))

    def numero_l(self, canvas, doc):
        canvas.setFont("Arial", 10)
        L = landscape(A4)
        canvas.drawRightString(L[0] - 2 * cm, L[1] - 2 * cm, str(self.num()))

    def afterFlowable(self, f):
        if not isinstance(f, Paragraph):
            return
        if getattr(f, "_toc", None) is not None:
            nivel, texto = f._toc
            chave = f"s{id(f)}"
            self.canv.bookmarkPage(chave)
            self.canv.addOutlineEntry(texto, chave, level=min(nivel, 2))
            self.notify("TOC", (nivel, texto, self.num(), chave))
        if getattr(f, "_lista", None) is not None:
            tipo, texto = f._lista
            chave = f"l{id(f)}"
            self.canv.bookmarkPage(chave)
            self.notify(tipo, (0, texto, self.num(), chave))


# ---------------------------------------------------------------- auxiliares
def titulo(numero, texto, nivel):
    """Hierarquia NBR 6024: primária em maiúsculas e negrito, secundária em maiúsculas,
    terciária em negrito com minúsculas."""
    if nivel == 0:
        rotulo, estilo = f"{numero} {texto.upper()}", h1
    elif nivel == 1:
        rotulo, estilo = f"{numero} {texto.upper()}", h2
    else:
        rotulo, estilo = f"{numero} {texto}", h3
    par = Paragraph(rotulo, estilo)
    par._toc = (nivel, rotulo)
    return par


def titulo_sem_numero(texto, no_sumario=True):
    par = Paragraph(texto, sem_ind)
    if no_sumario:
        par._toc = (0, texto)
    return par


num_fig, num_quadro = [0], [0]


def figura(arquivo, descricao, largura_max=LARG, altura_max=20 * cm, fonte_txt="Elaborada pelo autor (2026)."):
    num_fig[0] += 1
    w, h = PILImage.open(arquivo).size
    escala = min(largura_max / w, altura_max / h)
    img = Image(arquivo, width=w * escala, height=h * escala)
    leg = Paragraph(f"Figura {num_fig[0]} – {descricao}", legenda)
    leg._lista = ("FIG", f"Figura {num_fig[0]} – {descricao}")
    return KeepTogether([leg, Spacer(1, 4), img, Paragraph(f"Fonte: {fonte_txt}", fonte)])


def quadro(cabecalho, linhas, larguras, descricao):
    """Quadro: dados textuais, bordas fechadas (NBR 14724, 5.8)."""
    num_quadro[0] += 1
    dados = [[Paragraph(c, cel_b) for c in cabecalho]]
    dados += [[Paragraph(str(c), cel) for c in linha] for linha in linhas]
    t = Table(dados, colWidths=larguras, repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    leg = Paragraph(f"Quadro {num_quadro[0]} – {descricao}", legenda)
    leg._lista = ("QUA", f"Quadro {num_quadro[0]} – {descricao}")
    return [KeepTogether([leg, Spacer(1, 4), t, Paragraph("Fonte: Elaborado pelo autor (2026).", fonte)])]


def p(texto):
    return Paragraph(texto, corpo)


def alineas(itens):
    """Alíneas NBR 6024: letras minúsculas seguidas de parêntese, ponto e vírgula e ponto final."""
    letras = "abcdefghijklmnopqrstuvwxyz"
    return [Paragraph(t, alinea, bulletText=f"{letras[i]})") for i, t in enumerate(itens)]


ESTILO_SUM = [
    ParagraphStyle("s0", fontName="Arial-B", fontSize=12, leading=18),
    ParagraphStyle("s1", fontName="Arial", fontSize=12, leading=18),
    ParagraphStyle("s2", fontName="Arial-B", fontSize=12, leading=18),
]
ESTILO_LISTA = [ParagraphStyle("l0", fontName="Arial", fontSize=12, leading=18)]

story = []

# ================================================================ PRÉ-TEXTUAIS
# Capa (modelo UniFil). Logo, faixas, cidade e ano são desenhados em desenhar_capa.
titulo_capa = ParagraphStyle("titulo_capa", fontName="Arial-B", fontSize=14, leading=20, alignment=TA_CENTER)
autor_capa = ParagraphStyle("autor_capa", fontName="Arial", fontSize=12, leading=18, alignment=TA_CENTER)
story += [
    Spacer(1, 3.6 * cm),
    Paragraph(AUTOR, autor_capa),
]
if CURSO:
    story += [Paragraph(CURSO, autor_capa)]
story += [
    Spacer(1, 5.2 * cm),
    Paragraph(f"{TITULO}: {SUBTITULO.upper()}", titulo_capa),
    NextPageTemplate("pre"),
    PageBreak(),
]

# Folha de rosto
story += [
    Spacer(1, 3.6 * cm),
    Paragraph(AUTOR, autor_capa),
    Spacer(1, 5.2 * cm),
    Paragraph(f"{TITULO}: {SUBTITULO.upper()}", titulo_capa),
    Spacer(1, 2 * cm),
    Paragraph("Trabalho apresentado às disciplinas de Projeto de Desenvolvimento de Software I e II do "
              "Centro Universitário Filadélfia (UniFil), como requisito parcial para aprovação.", natureza),
    Spacer(1, 12),
    Paragraph(f"Professor: {PROFESSOR}.", natureza),
    Spacer(1, 4.3 * cm),
    Paragraph(CIDADE.title(), centro_n),
    Paragraph(ANO, centro_n),
    PageBreak(),
]

# Resumo (NBR 6028)
story += [
    titulo_sem_numero("RESUMO", no_sumario=False),
    Paragraph(
        "Agências de marketing digital atendem diversos clientes simultaneamente e produzem um grande volume de "
        "publicações para redes sociais, cujo controle costuma ficar disperso entre planilhas e aplicativos de "
        "mensagem. Este trabalho apresenta o desenvolvimento do Pauta, um sistema web para gestão de clientes e de "
        "conteúdos de agências. O sistema permite cadastrar clientes, registrar os conteúdos planejados com título, "
        "formato, data de publicação e legenda, conduzir um fluxo de revisão entre o social media e o gestor, com "
        "histórico de aprovações e solicitações de ajuste, e consultar um calendário editorial mensal. Para a análise "
        "e o projeto foram levantados requisitos funcionais e não funcionais, regras de negócio e elaborados os "
        "diagramas de casos de uso, de atividade, de classes e de sequência da UML, além do diagrama entidade "
        "relacionamento. A implementação utilizou a linguagem Python com o framework Flask, o mapeamento objeto "
        "relacional do SQLAlchemy e o banco de dados relacional SQLite, com testes automatizados em Pytest e "
        "versionamento no GitHub. Como resultado, obteve-se uma aplicação funcional com operações completas de "
        "cadastro, consulta, alteração e exclusão, controle de acesso por perfil e rastreabilidade das revisões, "
        "demonstrando a aplicação prática das etapas de engenharia de software.", resumo),
    Spacer(1, 18),
    Paragraph("<b>Palavras-chave:</b> engenharia de software; UML; sistema web; Flask; gestão de conteúdo.", resumo),
    PageBreak(),
]

# Abstract
story += [
    titulo_sem_numero("ABSTRACT", no_sumario=False),
    Paragraph(
        "Digital marketing agencies serve several clients at the same time and produce a large volume of social "
        "media posts, whose control is often scattered across spreadsheets and messaging apps. This work presents "
        "the development of Pauta, a web system for managing an agency's clients and content. The system allows "
        "registering clients, recording planned posts with title, format, publication date and caption, running a "
        "review workflow between the social media analyst and the manager, with a history of approvals and change "
        "requests, and viewing a monthly editorial calendar. For analysis and design, functional and non-functional "
        "requirements and business rules were defined, and UML use case, activity, class and sequence diagrams were "
        "created, along with the entity relationship diagram. The implementation used the Python language with the "
        "Flask framework, SQLAlchemy object relational mapping and the SQLite relational database, with automated "
        "tests in Pytest and version control on GitHub. The result is a working application with complete create, "
        "read, update and delete operations, role based access control and traceable reviews, demonstrating the "
        "practical application of software engineering stages.", resumo),
    Spacer(1, 18),
    Paragraph("<b>Keywords:</b> software engineering; UML; web system; Flask; content management.", resumo),
    PageBreak(),
]

# Listas
story += [titulo_sem_numero("LISTA DE ILUSTRAÇÕES", no_sumario=False), Lista("FIG", ESTILO_LISTA), PageBreak()]
story += [titulo_sem_numero("LISTA DE QUADROS", no_sumario=False), Lista("QUA", ESTILO_LISTA), PageBreak()]

# Sumário
story += [titulo_sem_numero("SUMÁRIO", no_sumario=False), Lista("TOC", ESTILO_SUM),
          NextPageTemplate("texto"), PageBreak()]

# ================================================================ TEXTUAIS
story.append(titulo("1", "Introdução", 0))
story += [
    p("Agências de marketing digital atendem vários clientes ao mesmo tempo e produzem, toda semana, dezenas de "
      "publicações para redes sociais. Na prática, esse controle costuma ficar espalhado entre planilhas, grupos de "
      "mensagem e anotações soltas, o que dificulta saber o que já foi aprovado, o que está atrasado e o que vai ao ar "
      "em cada dia. Quando a revisão acontece por mensagem, os comentários do gestor se perdem e o histórico de "
      "decisões fica difícil de recuperar."),
    p("Este trabalho apresenta o <b>Pauta</b>, um sistema web para centralizar a gestão de clientes e de conteúdos de "
      "uma agência. O sistema permite cadastrar os clientes atendidos, registrar cada conteúdo planejado (título, "
      "formato, data de publicação e legenda), conduzir um fluxo de revisão entre o social media e o gestor e "
      "visualizar tudo em um calendário editorial mensal. Cada conteúdo passa pelos status Rascunho, Em revisão, "
      "Ajustes solicitados, Aprovado e Publicado, e toda revisão fica registrada com o comentário de quem revisou."),
    p("O sistema possui dois perfis de acesso. O <b>Social media</b> cria e edita conteúdos, envia para revisão, "
      "marca como publicado e consulta o calendário. O <b>Gestor</b> tem as mesmas permissões e, além delas, mantém o "
      "cadastro de clientes e aprova ou solicita ajustes nos conteúdos."),
    p("O objetivo geral do trabalho é desenvolver, documentar e implementar um sistema com operações completas de "
      "cadastro, consulta, alteração e exclusão (CRUD) integradas a um banco de dados relacional. Como objetivos "
      "específicos, buscou-se levantar os requisitos do sistema, modelá-lo com a UML, que segundo Guedes (2018) é "
      "a linguagem padrão para a modelagem de sistemas orientados a objetos, implementá-lo e validá-lo por meio "
      "de testes automatizados."),
    p("A stack escolhida para o desenvolvimento foi composta pelas seguintes tecnologias:"),
]
story += alineas([
    "Python 3 como linguagem de programação (PYTHON SOFTWARE FOUNDATION, 2024);",
    "Flask 3 como framework web, responsável pelas rotas, sessões e renderização das páginas (PALLETS, 2024a);",
    "Flask-SQLAlchemy como mapeamento objeto relacional entre as classes Python e as tabelas (PALLETS, 2024b);",
    "SQLite como banco de dados relacional, escolhido por não exigir servidor e funcionar em qualquer máquina (SQLITE, 2024);",
    "Jinja2, HTML e CSS na interface, com layout responsivo;",
    "Pytest para os testes automatizados dos casos de uso;",
    "PlantUML para a elaboração dos diagramas UML e do diagrama entidade relacionamento (PLANTUML, 2024);",
    "Git e GitHub para o versionamento e a entrega do código.",
])
story.append(p("O documento está organizado da seguinte forma: a seção 2 traz o desenvolvimento, com os requisitos, "
               "as regras de negócio, os diagramas e a implementação; a seção 3 apresenta a conclusão; e, por fim, "
               "estão as referências utilizadas."))
story.append(PageBreak())

story.append(titulo("2", "Desenvolvimento", 0))
story.append(p("Nesta seção estão os artefatos de análise e projeto do sistema, seguidos da descrição da "
               "implementação realizada na Parte II da disciplina. O processo seguiu as atividades fundamentais de "
               "especificação, projeto, implementação e validação descritas por Sommerville (2019)."))

story.append(titulo("2.1", "Requisitos funcionais", 1))
story.append(p("Requisitos funcionais são declarações dos serviços que o sistema deve fornecer e de como ele deve "
               "reagir a entradas específicas (SOMMERVILLE, 2019). O Quadro 1 relaciona cada requisito ao caso de "
               "uso que o atende."))
rf = [
    ("RF01", "Permitir que o usuário acesse o sistema informando e-mail e senha.", "UC01"),
    ("RF02", "Permitir que o usuário encerre a sessão (logout).", "UC01"),
    ("RF03", "Permitir ao gestor cadastrar clientes com nome, segmento, Instagram, e-mail e telefone.", "UC02"),
    ("RF04", "Listar os clientes cadastrados, com busca por nome.", "UC02"),
    ("RF05", "Permitir ao gestor editar os dados de um cliente.", "UC02"),
    ("RF06", "Permitir ao gestor excluir um cliente; caso ele tenha conteúdos vinculados, o sistema deve inativá-lo.", "UC02"),
    ("RF07", "Permitir cadastrar conteúdos com título, cliente, formato, data de publicação e legenda.", "UC03"),
    ("RF08", "Listar os conteúdos com filtros por cliente e por status.", "UC03"),
    ("RF09", "Permitir editar e excluir conteúdos de acordo com o status.", "UC03"),
    ("RF10", "Permitir enviar um conteúdo para revisão do gestor.", "UC03"),
    ("RF11", "Permitir ao gestor aprovar um conteúdo ou solicitar ajustes com comentário.", "UC04"),
    ("RF12", "Manter o histórico de revisões de cada conteúdo.", "UC04"),
    ("RF13", "Permitir marcar um conteúdo aprovado como publicado.", "UC03"),
    ("RF14", "Exibir o calendário editorial mensal, com navegação entre meses e filtro por cliente.", "UC05"),
    ("RF15", "Exibir um painel com a quantidade de conteúdos por status e as próximas publicações.", "UC05"),
]
story += quadro(["Código", "Descrição", "Caso de uso"], rf, [2 * cm, LARG - 4.6 * cm, 2.6 * cm], "Requisitos funcionais")

story.append(titulo("2.2", "Requisitos não funcionais", 1))
story.append(p("Os requisitos não funcionais são restrições sobre os serviços ou funções oferecidos pelo sistema, "
               "como restrições de tempo, de processo de desenvolvimento e de padrões (SOMMERVILLE, 2019). Eles "
               "estão relacionados no Quadro 2."))
rnf = [
    ("RNF01", "Usabilidade", "A interface deve ser em português do Brasil e funcionar em computadores e celulares (layout responsivo)."),
    ("RNF02", "Segurança", "As senhas devem ser armazenadas apenas como hash, nunca em texto puro."),
    ("RNF03", "Segurança", "Todas as páginas, exceto o login, devem exigir usuário autenticado."),
    ("RNF04", "Segurança", "As ações de gestão de clientes e revisão devem ser restritas ao perfil Gestor."),
    ("RNF05", "Segurança", "Todos os formulários devem ser protegidos contra CSRF por token de sessão."),
    ("RNF06", "Persistência", "Os dados devem ser armazenados em banco de dados relacional (SQLite)."),
    ("RNF07", "Portabilidade", "O sistema deve rodar em Windows, Linux e macOS com Python 3.10 ou superior."),
    ("RNF08", "Manutenibilidade", "O código deve ser versionado no GitHub e possuir testes automatizados dos casos de uso."),
    ("RNF09", "Desempenho", "As páginas de listagem devem responder em menos de 2 segundos com até 1.000 conteúdos."),
]
story += quadro(["Código", "Categoria", "Descrição"], rnf, [2 * cm, 3.2 * cm, LARG - 5.2 * cm], "Requisitos não funcionais")

story.append(titulo("2.3", "Regras de negócio", 1))
story.append(p("As regras de negócio que orientam o comportamento do sistema são:"))
story += alineas([
    "RN01: todo conteúdo nasce com o status Rascunho;",
    "RN02: só conteúdos em Rascunho ou com Ajustes solicitados podem ser editados ou enviados para revisão;",
    "RN03: ao solicitar ajustes, o gestor é obrigado a escrever um comentário;",
    "RN04: só conteúdos Aprovados podem ser marcados como Publicados;",
    "RN05: conteúdos Publicados não podem ser excluídos;",
    "RN06: cliente com conteúdo vinculado não é excluído, e sim inativado, para preservar o histórico;",
    "RN07: clientes inativos não aparecem como opção no cadastro de novos conteúdos.",
])

story.append(PageBreak())
story.append(titulo("2.4", "Diagrama de casos de uso", 1))
story.append(p("O diagrama de casos de uso apresenta uma visão externa do sistema, identificando os atores e as "
               "funcionalidades que eles utilizam (GUEDES, 2018). O sistema possui dois atores. O Gestor é uma "
               "especialização do Social media: herda todos os casos de uso dele e acrescenta a gestão de clientes "
               "e a revisão de conteúdos. Todos os casos de uso dependem da autenticação (relação include), e o envio "
               "para revisão é uma extensão da manutenção de conteúdos, conforme a Figura 1."))
story.append(figura(os.path.join(DIAG, "01_caso_de_uso.png"), "Diagrama de casos de uso do sistema Pauta"))
ucs = [
    ("UC01", "Autenticar no sistema", "Social media, Gestor", "O usuário informa e-mail e senha e, se estiverem corretos, acessa o painel."),
    ("UC02", "Manter clientes", "Gestor", "Cadastrar, listar, editar e excluir (ou inativar) clientes da agência."),
    ("UC03", "Manter conteúdos", "Social media, Gestor", "Cadastrar, listar, editar, excluir, enviar para revisão e marcar conteúdos como publicados."),
    ("UC04", "Revisar conteúdo", "Gestor", "Aprovar um conteúdo em revisão ou solicitar ajustes com comentário, gerando registro no histórico."),
    ("UC05", "Consultar calendário editorial", "Social media, Gestor", "Visualizar os conteúdos de um mês em formato de calendário, com filtro por cliente."),
]
story.append(p("A descrição resumida de cada caso de uso está no Quadro 3."))
story += quadro(["Código", "Caso de uso", "Ator", "Descrição"], ucs,
                [1.6 * cm, 3.4 * cm, 3 * cm, LARG - 8 * cm], "Descrição resumida dos casos de uso")

story.append(PageBreak())
story.append(titulo("2.5", "Diagrama entidade relacionamento", 1))
story.append(p("O modelo de dados foi elaborado a partir das entidades identificadas nos requisitos, seguindo a "
               "abordagem entidade relacionamento (HEUSER, 2009). O banco possui quatro tabelas: um cliente possui "
               "vários conteúdos; cada conteúdo tem um usuário responsável; e cada conteúdo recebe várias revisões, "
               "sendo cada revisão feita por um usuário com perfil Gestor. Os campos marcados com asterisco são "
               "obrigatórios (NOT NULL), conforme a Figura 2."))
story.append(figura(os.path.join(DIAG, "02_der.png"), "Diagrama entidade relacionamento", altura_max=16.5 * cm))

story.append(PageBreak())
story.append(titulo("2.6", "Diagrama de atividade", 1))
story.append(p("A Figura 3 representa o processo principal do sistema: a produção de um conteúdo, desde o cadastro "
               "pelo social media até a publicação, passando pelo ciclo de revisão com o gestor, que pode se repetir "
               "até o conteúdo ser aprovado. As raias separam as atividades de cada ator."))
story.append(figura(os.path.join(DIAG, "03_atividade.png"),
                    "Diagrama de atividade do fluxo de produção e aprovação de conteúdo", altura_max=18 * cm))

story.append(PageBreak())
story.append(titulo("2.7", "Diagrama de classes", 1))
story.append(p("O diagrama de classes é focado nas entidades do domínio. As classes Usuario, Cliente, Conteudo e "
               "Revisao correspondem diretamente às tabelas do diagrama entidade relacionamento e estão "
               "implementadas no arquivo models.py. A relação entre Conteudo e Revisao é uma composição, pois as "
               "revisões não existem sem o conteúdo e são removidas junto com ele. As enumerações representam os "
               "valores permitidos de status, formato e perfil (Figura 4)."))
story.append(figura(os.path.join(DIAG, "04_classes.png"), "Diagrama de classes das entidades", altura_max=17.5 * cm))

story.append(PageBreak())
story.append(titulo("2.8", "Diagramas de sequência", 1))
story.append(p("O diagrama de sequência mostra a ordem temporal das mensagens trocadas entre os objetos durante um "
               "processo (GUEDES, 2018). Para cada caso de uso foi elaborado um diagrama, seguindo o padrão "
               "boundary, control e entity: a tela (boundary) recebe a ação do ator, a rota do Flask (control) "
               "aplica as regras e as entidades acessam o banco de dados por meio do mapeamento objeto relacional. "
               "Os diagramas estão nas Figuras 5 a 9, apresentados em páginas na orientação paisagem para "
               "preservar a legibilidade."))
seqs = [
    ("05_seq_uc01.png", "2.8.1", "UC01 Autenticar no sistema"),
    ("06_seq_uc02.png", "2.8.2", "UC02 Manter clientes"),
    ("07_seq_uc03.png", "2.8.3", "UC03 Manter conteúdos"),
    ("08_seq_uc04.png", "2.8.4", "UC04 Revisar conteúdo"),
    ("09_seq_uc05.png", "2.8.5", "UC05 Consultar calendário editorial"),
]
story.append(NextPageTemplate("deitada"))
for i, (arq, num, nome) in enumerate(seqs):
    story.append(PageBreak())
    story.append(titulo(num, nome, 2))
    if i == len(seqs) - 1:
        story.append(NextPageTemplate("texto"))
    story.append(figura(os.path.join(DIAG, arq), f"Diagrama de sequência do {nome}",
                        largura_max=LARG_L, altura_max=12.2 * cm))

story.append(PageBreak())
story.append(titulo("2.9", "Implementação", 1))
story.append(p("A implementação foi feita seguindo os artefatos apresentados. O código está organizado em um pacote "
               "Python chamado pauta, com a seguinte estrutura:"))
story += alineas([
    "models.py: classes Usuario, Cliente, Conteudo e Revisao, com os métodos do diagrama de classes;",
    "__init__.py: criação da aplicação, controle de sessão e de CSRF e as rotas de cada caso de uso;",
    "templates: telas em Jinja2 (login, painel, clientes, conteúdos e calendário);",
    "seed.py: dados de exemplo para demonstração;",
    "tests/test_app.py: oito testes automatizados que cobrem os cinco casos de uso e as regras de negócio.",
])
story.append(p("As operações de CRUD estão presentes em duas entidades. Para clientes, as rotas /clientes/novo, "
               "/clientes, /clientes/{id}/editar e /clientes/{id}/excluir realizam a criação, a leitura, a "
               "atualização e a exclusão. Para conteúdos, as rotas equivalentes ficam em /conteudos. O banco é "
               "criado automaticamente na primeira execução, e as instruções para rodar o projeto estão no arquivo "
               "README.md do repositório no GitHub. As principais telas do sistema estão nas Figuras 10 a 16."))
telas = [
    ("01_login.png", "Tela de login (UC01)"),
    ("02_painel.png", "Painel com resumo por status e próximas publicações"),
    ("03_clientes.png", "Listagem de clientes (UC02)"),
    ("04_cliente_form.png", "Formulário de cadastro de cliente (UC02)"),
    ("05_conteudos.png", "Listagem de conteúdos com filtros (UC03)"),
    ("06_revisao.png", "Detalhe do conteúdo com a área de revisão do gestor (UC04)"),
    ("07_calendario.png", "Calendário editorial mensal (UC05)"),
]
for arq, desc in telas:
    story.append(figura(os.path.join(TELAS, arq), desc, altura_max=10 * cm,
                        fonte_txt="Captura de tela do sistema desenvolvido pelo autor (2026)."))

story.append(PageBreak())
story.append(titulo("3", "Conclusão", 0))
story += [
    p("O desenvolvimento do Pauta permitiu aplicar na prática o caminho completo de um projeto de software: entender "
      "o problema, transformar isso em requisitos, modelar o sistema com UML e só então partir para o código. "
      "Ficou claro como a modelagem antes da implementação economiza retrabalho. O diagrama de classes e o diagrama "
      "entidade relacionamento, por exemplo, viraram quase diretamente o arquivo de modelos, e os diagramas de "
      "sequência serviram de roteiro para escrever cada rota, o que confirma a importância das atividades de "
      "projeto destacada por Pressman e Maxim (2021)."),
    p("Outro aprendizado importante foi a definição das regras de negócio. Questões que pareciam simples, como o que "
      "fazer ao excluir um cliente que já tem conteúdos, só apareceram durante a modelagem, e a solução de inativar "
      "o cliente preservou o histórico sem quebrar a integridade do banco. O fluxo de status do conteúdo também "
      "mostrou a importância de deixar explícito, no código e na documentação, quais transições são permitidas."),
    p("Na parte técnica, o projeto consolidou o uso do Flask com um mapeamento objeto relacional, o controle de "
      "sessão e de permissões por perfil, a proteção de formulários e a escrita de testes automatizados, que deram "
      "segurança para ajustar o código sem quebrar o que já funcionava. O versionamento no GitHub completou a "
      "entrega."),
    p("Como trabalhos futuros, o sistema pode evoluir com o envio de imagens e vídeos de cada conteúdo, "
      "notificações por e-mail quando um conteúdo for revisado, integração com as APIs das redes sociais para "
      "agendamento automático e relatórios de produtividade por responsável."),
]

# ================================================================ PÓS-TEXTUAIS
story.append(PageBreak())
story.append(titulo_sem_numero("REFERÊNCIAS"))
refs = [  # NBR 6023:2018, ordem alfabética
    "GUEDES, Gilleanes T. A. <b>UML 2</b>: uma abordagem prática. 3. ed. São Paulo: Novatec, 2018.",
    "HEUSER, Carlos Alberto. <b>Projeto de banco de dados</b>. 6. ed. Porto Alegre: Bookman, 2009.",
    "PALLETS. <b>Flask documentation</b>: version 3.1.x. [<i>S. l.</i>]: Pallets, 2024a. Disponível em: "
    "https://flask.palletsprojects.com. Acesso em: 5 nov. 2026.",
    "PALLETS. <b>Flask-SQLAlchemy documentation</b>. [<i>S. l.</i>]: Pallets, 2024b. Disponível em: "
    "https://flask-sqlalchemy.readthedocs.io. Acesso em: 5 nov. 2026.",
    "PLANTUML. <b>PlantUML language reference guide</b>. [<i>S. l.</i>]: PlantUML, 2024. Disponível em: "
    "https://plantuml.com. Acesso em: 5 nov. 2026.",
    "PRESSMAN, Roger S.; MAXIM, Bruce R. <b>Engenharia de software</b>: uma abordagem profissional. 9. ed. "
    "Porto Alegre: AMGH, 2021.",
    "PYTHON SOFTWARE FOUNDATION. <b>Python 3 documentation</b>. [<i>S. l.</i>]: PSF, 2024. Disponível em: "
    "https://docs.python.org/3. Acesso em: 5 nov. 2026.",
    "SOMMERVILLE, Ian. <b>Engenharia de software</b>. 10. ed. São Paulo: Pearson, 2019.",
    "SQLITE. <b>SQLite documentation</b>. [<i>S. l.</i>]: SQLite, 2024. Disponível em: "
    "https://www.sqlite.org/docs.html. Acesso em: 5 nov. 2026.",
]
story += [Paragraph(r, ref) for r in refs]

doc = Documento(SAIDA)
doc.pageTemplates.sort(key=lambda t: t.id != 'capa')
doc.multiBuild(story)
print("ok", SAIDA)
