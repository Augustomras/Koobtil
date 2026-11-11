from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.db.models import Count, Q #isso aqui é para buscra tudo

import calendar
from django.utils import timezone #pro desafio 
from datetime import timedelta #pro dias consecutivos

from .forms import CadastroForm, LivroForm, ResenhaForm, PAISES
from .models import Livro, Resenha, Perfil, VisualizacaoLivro, Denuncia

from django.views.decorators.http import require_POST # pro negocio de denuncia do admin la 

def cadastro(request):
    if request.method == 'POST':
        form = CadastroForm(request.POST)

        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect('core:home')

    else:
        form = CadastroForm()

    return render(
        request,
        'registration/cadastro.html',
        {'form': form}
    )


def termos(request):
    return render(request, 'termos_de_uso.html')


def privacidade(request):
    return render(request, 'politica_privacidade.html')


def landing(request):
    # Informações exibidas na tela inicial
    total_livros = Livro.objects.count()

    total_usuarios = get_user_model().objects.count()

    total_paises = Perfil.objects.exclude(
        pais__isnull=True
    ).exclude(
        pais=''
    ).values('pais').distinct().count()

    return render(request, 'core/landing.html', {
        'total_livros': total_livros,
        'total_usuarios': total_usuarios,
        'total_paises': total_paises,
    })
@login_required
def home(request):
    livros = Livro.objects.order_by('?')[:3]

    livros_populares = Livro.objects.annotate(
        total_favoritos=Count('favoritado_por')
    ).order_by('-total_favoritos')[:5]

    resenhas = Resenha.objects.select_related(
        'usuario', 'livro'
    ).order_by('-data_publicacao')[:5]

    Usuario = get_user_model()
    leitores = Usuario.objects.filter(is_active=True)

    hoje = timezone.localdate()

    
    # SEQUÊNCIA DE VISUALIZAÇÃO DE LIVROS
    datas_visualizacao = set(
        VisualizacaoLivro.objects.filter(
            usuario=request.user
        ).values_list('data_visualizacao', flat=True)
    )

    sequencia = 0

    if datas_visualizacao:
        ultima_data = max(datas_visualizacao)

        if ultima_data >= hoje - timedelta(days=1):
            data_atual = ultima_data

            while data_atual in datas_visualizacao:
                sequencia += 1
                data_atual -= timedelta(days=1)


    desafios = [
        {
            'titulo': 'Crítico literário',
            'descricao': 'Publique 5 resenhas este mês.',
            'meta': 5,
            'tipo': 'resenhas',
        },
        {
            'titulo': 'Leitor dedicado',
            'descricao': 'Publique 8 resenhas este mês.',
            'meta': 8,
            'tipo': 'resenhas',
        },
        {
            'titulo': 'Explorador literário',
            'descricao': 'Avalie livros de 3 autores diferentes.',
            'meta': 3,
            'tipo': 'autores',
        },
        {
            'titulo': 'Voz da comunidade',
            'descricao': 'Publique 10 resenhas este mês.',
            'meta': 10,
            'tipo': 'resenhas',
        },
    ]

    desafio = desafios[(hoje.month - 1) % len(desafios)]

    resenhas_mes = Resenha.objects.filter(
        usuario=request.user,
        data_publicacao__year=hoje.year,
        data_publicacao__month=hoje.month
    )

    if desafio['tipo'] == 'resenhas':
        progresso = resenhas_mes.count()
    else:
        progresso = resenhas_mes.values(
            'livro__autor'
        ).distinct().count()

    porcentagem = min(
        int((progresso / desafio['meta']) * 100),
        100
    )

    ultimo_dia = calendar.monthrange(
        hoje.year, hoje.month
    )[1]

    dias_restantes = ultimo_dia - hoje.day

    return render(request, 'core/home.html', {
        'livros': livros,
        'resenhas': resenhas,
        'leitores': leitores,
        'desafio': desafio,
        'progresso': progresso,
        'porcentagem': porcentagem,
        'dias_restantes': dias_restantes,
        'sequencia': sequencia,
        'livros_populares': livros_populares,
    })

@login_required
def explorar(request):
    livros = Livro.objects.all()

    dificuldade = request.GET.get('dificuldade')

    if dificuldade:
        livros = livros.filter(nivel_dificuldade=dificuldade)

    destaque_semana = Livro.objects.annotate(
        total_favoritos=Count('favoritado_por')
    ).filter(
        total_favoritos__gt=0
    ).order_by('-total_favoritos').first()

    return render(request, 'core/explorar.html', {
        'livros': livros,
        'destaque_semana': destaque_semana,
        'dificuldade_selecionada': dificuldade,
    })


@login_required
def perfil(request):
    leitor = request.user
    perfil = leitor.perfil

    resenhas = Resenha.objects.filter(
        usuario=leitor
    ).select_related('livro').order_by('-data_publicacao')

    return render(request, 'core/perfil.html', {
        'leitor': leitor,
        'perfil': perfil,
        'resenhas': resenhas,
        'total_resenhas': resenhas.count(),
    })



def adicionar_livro(request):
    return render(request, 'core/livro.html')

def detalhe_livro(request, livro_id):
    livro = get_object_or_404(Livro, id=livro_id)

    return render(request, 'core/detalhe_livro.html', {
        'livro': livro
    })

@login_required
def perfil_leitor(request, usuario_id):
    Usuario = get_user_model()
    leitor = get_object_or_404(Usuario, id=usuario_id)

    perfil, criado = Perfil.objects.get_or_create(
    usuario=leitor,
    defaults={
        'nome_completo': leitor.get_full_name() or leitor.username
    }
)

    resenhas = Resenha.objects.filter(
        usuario=leitor
    ).select_related('livro').order_by('-data_publicacao')

    favoritos = perfil.livros_favoritos.all()

    return render(request, 'core/perfil.html', {
        'leitor': leitor,
        'perfil': perfil,
        'resenhas': resenhas,
        'total_resenhas': resenhas.count(),
        'favoritos': favoritos,
    })
