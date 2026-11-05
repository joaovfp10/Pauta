"""Gera docs/Documentacao_Pauta.pdf a partir dos diagramas e telas."""
import os

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
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
SAIDA = os.path.join(AQUI, "Documentacao_Pauta.pdf")

F = "/usr/share/fonts/truetype/liberation/"
pdfmetrics.registerFont(TTFont("Arial", F + "LiberationSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Arial-B", F + "LiberationSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Arial-I", F + "LiberationSans-Italic.ttf"))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-B", italic="Arial-I", boldItalic="Arial-B")

VERDE = colors.HexColor("#1f6f5c")

corpo = ParagraphStyle("corpo", fontName="Arial", fontSize=12, leading=18, alignment=TA_JUSTIFY,
                       firstLineIndent=1.25 * cm, spaceAfter=6)
corpo_sem = ParagraphStyle("corpo_sem", parent=corpo, firstLineIndent=0)
item = ParagraphStyle("item", parent=corpo, firstLineIndent=0, leftIndent=0.8 * cm, bulletIndent=0.3 * cm, spaceAfter=3)
h1 = ParagraphStyle("h1", fontName="Arial-B", fontSize=12, leading=18, spaceBefore=0, spaceAfter=12)
h2 = ParagraphStyle("h2", fontName="Arial-B", fontSize=12, leading=18, spaceBefore=12, spaceAfter=8)
h3 = ParagraphStyle("h3", fontName="Arial", fontSize=12, leading=18, spaceBefore=10, spaceAfter=6)
legenda = ParagraphStyle("legenda", fontName="Arial", fontSize=10, leading=13, alignment=TA_CENTER, spaceBefore=4, spaceAfter=2)
fonte = ParagraphStyle("fonte", parent=legenda, spaceBefore=0, spaceAfter=14)
cel = ParagraphStyle("cel", fontName="Arial", fontSize=10, leading=13)
cel_b = ParagraphStyle("cel_b", parent=cel, fontName="Arial-B", textColor=colors.white)
centro = ParagraphStyle("centro", fontName="Arial-B", fontSize=12, leading=18, alignment=TA_CENTER)
ref = ParagraphStyle("ref", fontName="Arial", fontSize=12, leading=14, spaceAfter=12)

LARG = A4[0] - 3 * cm - 2 * cm


class Documento(BaseDocTemplate):
    def __init__(self, arquivo):
        super().__init__(arquivo, pagesize=A4, leftMargin=3 * cm, rightMargin=2 * cm,
                         topMargin=3 * cm, bottomMargin=2 * cm,
                         title="Pauta: Sistema de Gestão de Clientes e Conteúdo",
                         author="João Victor Ferreira Pinto")
        quadro = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="q")
        L = landscape(A4)
        quadro_l = Frame(2.5 * cm, 2 * cm, L[0] - 4.5 * cm, L[1] - 4.5 * cm, id="ql")
        self.addPageTemplates([
            PageTemplate(id="sem_numero", frames=[quadro]),
            PageTemplate(id="numerada", frames=[quadro], onPage=self.numero),
            PageTemplate(id="deitada", frames=[quadro_l], onPage=self.numero_l, pagesize=L),
        ])
        self.contador_figura = 0

    def numero(self, canvas, doc):
        canvas.setFont("Arial", 10)
        canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 2 * cm, str(doc.page))

    def numero_l(self, canvas, doc):
        canvas.setFont("Arial", 10)
        L = landscape(A4)
        canvas.drawRightString(L[0] - 2 * cm, L[1] - 1.8 * cm, str(doc.page))

    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and getattr(f, "_toc_nivel", None) is not None:
            texto = f.getPlainText()
            chave = f"s{id(f)}"
            self.canv.bookmarkPage(chave)
            self.canv.addOutlineEntry(texto, chave, level=f._toc_nivel)
            self.notify("TOCEntry", (f._toc_nivel, texto, self.page, chave))


def titulo(texto, nivel):
    estilo = {0: h1, 1: h2, 2: h3}[nivel]
    p = Paragraph(texto, estilo)
    p._toc_nivel = nivel
    return p


num_fig = [0]


def figura(arquivo, descricao, largura_max=LARG, altura_max=21 * cm, fonte_txt="Elaborado pelo autor (2026)."):
    num_fig[0] += 1
    w, h = PILImage.open(arquivo).size
    escala = min(largura_max / w, altura_max / h)
    img = Image(arquivo, width=w * escala, height=h * escala)
    return KeepTogether([
        Paragraph(f"Figura {num_fig[0]}: {descricao}", legenda),
        Spacer(1, 4), img,
        Paragraph(f"Fonte: {fonte_txt}", fonte),
    ])


num_tab = [0]


def tabela(cabecalho, linhas, larguras, descricao):
    num_tab[0] += 1
    dados = [[Paragraph(c, cel_b) for c in cabecalho]]
    dados += [[Paragraph(str(c), cel) for c in linha] for linha in linhas]
    t = Table(dados, colWidths=larguras, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9fb8af")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f7f5")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return [KeepTogether([Paragraph(f"Tabela {num_tab[0]}: {descricao}", legenda), Spacer(1, 4), t,
            Paragraph("Fonte: Elaborado pelo autor (2026).", fonte)])]


def p(texto):
    return Paragraph(texto, corpo)


def lista(itens):
    return [Paragraph(i, item, bulletText="•") for i in itens]


# ---------------------------------------------------------------- conteúdo
story = []

# Capa
story += [
    Paragraph("CENTRO UNIVERSITÁRIO FILADÉLFIA (UNIFIL)", centro),
    Spacer(1, 6),
    Paragraph("PROJETO DE DESENVOLVIMENTO DE SOFTWARE I E II", centro),
    Spacer(1, 3.5 * cm),
    Paragraph("JOÃO VICTOR FERREIRA PINTO", centro),
    Spacer(1, 6 * cm),
    Paragraph("PAUTA: SISTEMA DE GESTÃO DE CLIENTES E CONTEÚDO", centro),
    Spacer(1, 6),
    Paragraph("PARA AGÊNCIAS DE MARKETING DIGITAL", centro),
    Spacer(1, 1.2 * cm),
    Paragraph("Trabalho individual", ParagraphStyle("x", parent=centro, fontName="Arial")),
    Spacer(1, 7 * cm),
    Paragraph("LONDRINA", centro),
    Paragraph("2026", centro),
    PageBreak(),
]

# Sumário
toc = TableOfContents()
toc.dotsMinLevel = 0
toc.levelStyles = [
    ParagraphStyle("t0", fontName="Arial-B", fontSize=12, leading=18, leftIndent=0, firstLineIndent=0),
    ParagraphStyle("t1", fontName="Arial", fontSize=12, leading=18, leftIndent=0.6 * cm, firstLineIndent=0),
    ParagraphStyle("t2", fontName="Arial", fontSize=11, leading=16, leftIndent=1.2 * cm, firstLineIndent=0),
]
story += [Paragraph("SUMÁRIO", centro), Spacer(1, 18), toc, NextPageTemplate("numerada"), PageBreak()]

# 1 Introdução
story.append(titulo("1 INTRODUÇÃO", 0))
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
    p("A stack escolhida para o desenvolvimento foi:"),
]
story += lista([
    "<b>Python 3</b> como linguagem de programação;",
    "<b>Flask 3</b> como framework web, responsável pelas rotas, sessões e renderização das páginas;",
    "<b>Flask-SQLAlchemy</b> como ORM, fazendo o mapeamento entre as classes Python e as tabelas;",
    "<b>SQLite</b> como banco de dados relacional, escolhido por não exigir servidor e funcionar em qualquer máquina;",
    "<b>Jinja2, HTML e CSS</b> na interface, com layout responsivo;",
    "<b>Pytest</b> para os testes automatizados dos casos de uso;",
    "<b>PlantUML</b> para a criação dos diagramas UML e do DER;",
    "<b>Git e GitHub</b> para versionamento e entrega do código.",
])
story.append(p("O documento está organizado da seguinte forma: o capítulo 2 traz o desenvolvimento, com os "
               "requisitos, regras de negócio, diagramas e a implementação; o capítulo 3 apresenta a conclusão; e, "
               "por fim, estão as referências utilizadas."))
story.append(PageBreak())

# 2 Desenvolvimento
story.append(titulo("2 DESENVOLVIMENTO", 0))
story.append(p("Neste capítulo estão os artefatos de análise e projeto do sistema, seguidos da descrição da "
               "implementação realizada na Parte II da disciplina."))

story.append(titulo("2.1 Requisitos funcionais", 1))
story.append(p("Os requisitos funcionais descrevem o que o sistema deve fazer. A Tabela 1 relaciona cada requisito "
               "ao caso de uso que o atende."))
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
story += tabela(["Código", "Descrição", "Caso de uso"], rf, [2 * cm, LARG - 4.6 * cm, 2.6 * cm], "Requisitos funcionais")

story.append(titulo("2.2 Requisitos não funcionais", 1))
story.append(p("Os requisitos não funcionais definem restrições e qualidades que o sistema deve atender."))
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
story += tabela(["Código", "Categoria", "Descrição"], rnf, [2 * cm, 3.2 * cm, LARG - 5.2 * cm], "Requisitos não funcionais")

story.append(titulo("2.3 Regras de negócio", 1))
story += lista([
    "<b>RN01:</b> todo conteúdo nasce com o status Rascunho.",
    "<b>RN02:</b> só conteúdos em Rascunho ou com Ajustes solicitados podem ser editados ou enviados para revisão.",
    "<b>RN03:</b> ao solicitar ajustes, o gestor é obrigado a escrever um comentário.",
    "<b>RN04:</b> só conteúdos Aprovados podem ser marcados como Publicados.",
    "<b>RN05:</b> conteúdos Publicados não podem ser excluídos.",
    "<b>RN06:</b> cliente com conteúdo vinculado não é excluído, e sim inativado, para preservar o histórico.",
    "<b>RN07:</b> clientes inativos não aparecem como opção no cadastro de novos conteúdos.",
])

story.append(PageBreak())
story.append(titulo("2.4 Diagrama de casos de uso", 1))
story.append(p("O sistema possui dois atores. O Gestor é uma especialização do Social media: ele herda todos os casos "
               "de uso do Social media e acrescenta a gestão de clientes e a revisão de conteúdos. Todos os casos de "
               "uso dependem da autenticação (relação include), e o envio para revisão é uma extensão da manutenção "
               "de conteúdos."))
story.append(figura(os.path.join(DIAG, "01_caso_de_uso.png"), "Diagrama de casos de uso do sistema Pauta"))
ucs = [
    ("UC01", "Autenticar no sistema", "Social media, Gestor", "O usuário informa e-mail e senha e, se estiverem corretos, acessa o painel."),
    ("UC02", "Manter clientes", "Gestor", "Cadastrar, listar, editar e excluir (ou inativar) clientes da agência."),
    ("UC03", "Manter conteúdos", "Social media, Gestor", "Cadastrar, listar, editar, excluir, enviar para revisão e marcar conteúdos como publicados."),
    ("UC04", "Revisar conteúdo", "Gestor", "Aprovar um conteúdo em revisão ou solicitar ajustes com comentário, gerando registro no histórico."),
    ("UC05", "Consultar calendário editorial", "Social media, Gestor", "Visualizar os conteúdos de um mês em formato de calendário, com filtro por cliente."),
]
story += tabela(["Código", "Caso de uso", "Ator", "Descrição"], ucs,
                [1.6 * cm, 3.4 * cm, 3 * cm, LARG - 8 * cm], "Descrição resumida dos casos de uso")

story.append(PageBreak())
story.append(titulo("2.5 Diagrama Entidade Relacionamento (DER)", 1))
story.append(p("O banco de dados possui quatro tabelas. Um cliente possui vários conteúdos; cada conteúdo tem um "
               "usuário responsável; e cada conteúdo recebe várias revisões, sendo cada revisão feita por um usuário "
               "com perfil Gestor. Os campos marcados com asterisco são obrigatórios (NOT NULL)."))
story.append(figura(os.path.join(DIAG, "02_der.png"), "Diagrama Entidade Relacionamento", altura_max=17 * cm))

story.append(PageBreak())
story.append(titulo("2.6 Diagrama de atividade", 1))
story.append(p("O diagrama de atividade abaixo representa o processo principal do sistema: a produção de um conteúdo, "
               "desde o cadastro pelo social media até a publicação, passando pelo ciclo de revisão com o gestor, que "
               "pode se repetir até o conteúdo ser aprovado."))
story.append(figura(os.path.join(DIAG, "03_atividade.png"), "Diagrama de atividade do fluxo de produção e aprovação de conteúdo", altura_max=18.5 * cm))

story.append(PageBreak())
story.append(titulo("2.7 Diagrama de classes", 1))
story.append(p("O diagrama de classes é focado nas entidades do domínio. As classes Usuario, Cliente, Conteudo e "
               "Revisao correspondem diretamente às tabelas do DER e estão implementadas no arquivo models.py. A "
               "relação entre Conteudo e Revisao é uma composição, pois as revisões não existem sem o conteúdo e são "
               "removidas junto com ele. As enumerações representam os valores permitidos de status, formato e perfil."))
story.append(figura(os.path.join(DIAG, "04_classes.png"), "Diagrama de classes das entidades", altura_max=18 * cm))

story.append(PageBreak())
story.append(titulo("2.8 Diagramas de sequência", 1))
story.append(p("Para cada caso de uso foi elaborado um diagrama de sequência, seguindo o padrão boundary, control e "
               "entity: a tela (boundary) recebe a ação do ator, a rota do Flask (control) aplica as regras e as "
               "entidades acessam o banco de dados por meio do ORM."))
seqs = [
    ("05_seq_uc01.png", "2.8.1 UC01 Autenticar no sistema", "Diagrama de sequência do UC01 Autenticar no sistema"),
    ("06_seq_uc02.png", "2.8.2 UC02 Manter clientes", "Diagrama de sequência do UC02 Manter clientes"),
    ("07_seq_uc03.png", "2.8.3 UC03 Manter conteúdos", "Diagrama de sequência do UC03 Manter conteúdos"),
    ("08_seq_uc04.png", "2.8.4 UC04 Revisar conteúdo", "Diagrama de sequência do UC04 Revisar conteúdo"),
    ("09_seq_uc05.png", "2.8.5 UC05 Consultar calendário editorial", "Diagrama de sequência do UC05 Consultar calendário editorial"),
]
LARG_L = landscape(A4)[0] - 4.5 * cm
story.append(NextPageTemplate("deitada"))
for i, (arq, sub, desc) in enumerate(seqs):
    story.append(PageBreak())
    story.append(titulo(sub, 2))
    if i == len(seqs) - 1:
        story.append(NextPageTemplate("numerada"))
    story.append(figura(os.path.join(DIAG, arq), desc, largura_max=LARG_L, altura_max=13.6 * cm))

story.append(PageBreak())
story.append(titulo("2.9 Implementação", 1))
story.append(p("A implementação foi feita seguindo os artefatos acima. O código está organizado em um pacote Python "
               "chamado pauta, com a seguinte estrutura:"))
story += lista([
    "<b>models.py:</b> classes Usuario, Cliente, Conteudo e Revisao, com os métodos do diagrama de classes;",
    "<b>__init__.py:</b> criação da aplicação, controle de sessão e CSRF e as rotas de cada caso de uso;",
    "<b>templates:</b> telas em Jinja2 (login, painel, clientes, conteúdos e calendário);",
    "<b>seed.py:</b> dados de exemplo para demonstração;",
    "<b>tests/test_app.py:</b> oito testes automatizados cobrindo os cinco casos de uso e as regras de negócio.",
])
story.append(p("As operações de CRUD estão presentes em duas entidades. Para clientes, as rotas /clientes/novo, "
               "/clientes, /clientes/{id}/editar e /clientes/{id}/excluir realizam a criação, leitura, atualização e "
               "exclusão. Para conteúdos, as rotas equivalentes ficam em /conteudos. O banco é criado automaticamente "
               "na primeira execução e as instruções para rodar o projeto estão no arquivo README.md do repositório."))
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
    story.append(figura(os.path.join(TELAS, arq), desc, altura_max=10.5 * cm, fonte_txt="Captura de tela do sistema (2026)."))

# 3 Conclusão
story.append(PageBreak())
story.append(titulo("3 CONCLUSÃO", 0))
story += [
    p("O desenvolvimento do Pauta permitiu aplicar na prática o caminho completo de um projeto de software: entender "
      "o problema, transformar isso em requisitos, modelar o sistema com UML e só então partir para o código. "
      "Ficou claro como a modelagem antes da implementação economiza retrabalho. O diagrama de classes e o DER, por "
      "exemplo, viraram quase diretamente o arquivo de modelos, e os diagramas de sequência serviram de roteiro para "
      "escrever cada rota."),
    p("Outro aprendizado importante foi a definição das regras de negócio. Questões que pareciam simples, como o que "
      "fazer ao excluir um cliente que já tem conteúdos, só apareceram durante a modelagem, e a solução de inativar o "
      "cliente preservou o histórico sem quebrar a integridade do banco. O fluxo de status do conteúdo também "
      "mostrou a importância de deixar explícito, no código e na documentação, quais transições são permitidas."),
    p("Na parte técnica, o projeto consolidou o uso do Flask com um ORM, o controle de sessão e de permissões por "
      "perfil, a proteção de formulários e a escrita de testes automatizados, que deram segurança para ajustar o "
      "código sem quebrar o que já funcionava. O versionamento no GitHub completou a entrega."),
    p("Como trabalhos futuros, o sistema pode evoluir com o envio de imagens e vídeos de cada conteúdo, "
      "notificações por e-mail quando um conteúdo for revisado, integração com as APIs das redes sociais para "
      "agendamento automático e relatórios de produtividade por responsável."),
]

# Referências
story.append(PageBreak())
_r = Paragraph("REFERÊNCIAS", centro); _r._toc_nivel = 0
story.append(_r)
story.append(Spacer(1, 18))
refs = [
    "FLASK. <b>Flask Documentation (3.1.x)</b>. Pallets Projects, 2024. Disponível em: https://flask.palletsprojects.com. Acesso em: 5 nov. 2026.",
    "FLASK-SQLALCHEMY. <b>Flask-SQLAlchemy Documentation</b>. Pallets Eco, 2024. Disponível em: https://flask-sqlalchemy.readthedocs.io. Acesso em: 5 nov. 2026.",
    "GUEDES, Gilleanes T. A. <b>UML 2</b>: uma abordagem prática. 3. ed. São Paulo: Novatec, 2018.",
    "HEUSER, Carlos Alberto. <b>Projeto de banco de dados</b>. 6. ed. Porto Alegre: Bookman, 2009.",
    "PLANTUML. <b>PlantUML Language Reference Guide</b>. 2024. Disponível em: https://plantuml.com. Acesso em: 5 nov. 2026.",
    "PRESSMAN, Roger S.; MAXIM, Bruce R. <b>Engenharia de software</b>: uma abordagem profissional. 9. ed. Porto Alegre: AMGH, 2021.",
    "PYTHON SOFTWARE FOUNDATION. <b>Python 3 Documentation</b>. 2024. Disponível em: https://docs.python.org/3. Acesso em: 5 nov. 2026.",
    "SOMMERVILLE, Ian. <b>Engenharia de software</b>. 10. ed. São Paulo: Pearson, 2019.",
    "SQLITE. <b>SQLite Documentation</b>. 2024. Disponível em: https://www.sqlite.org/docs.html. Acesso em: 5 nov. 2026.",
]
story += [Paragraph(r, ref) for r in refs]

doc = Documento(SAIDA)
doc.multiBuild(story)
print("ok", SAIDA)
