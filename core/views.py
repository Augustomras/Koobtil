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

def home(request):
    livros = Livro.objects.all()
    resenhas = Resenha.objects.all()

    Usuario = get_user_model()
    leitores = Usuario.objects.filter(is_active=True)

    return render(request, 'core/home.html', {
        'livros': livros,
        'resenhas': resenhas,
        'leitores': leitores
    })

def explorar(request):
    livros = Livro.objects.all()

    return render(request, 'core/explorar.html', {
        'livros': livros
    })

def perfil(request):
    livros = Livro.objects.all()

    return render(request, 'core/perfil.html', {
        'livros': livros
    })

def adicionar_livro(request):
    return render(request, 'core/livro.html')

def detalhe_livro(request, livro_id):
    livro = get_object_or_404(Livro, id=livro_id)

    return render(request, 'core/detalhe_livro.html', {
        'livro': livro
    })

def perfil_leitor(request, usuario_id):
    Usuario = get_user_model()
    leitor = get_object_or_404(Usuario, id=usuario_id)

    return render(request, 'core/perfil.html', {
        'leitor': leitor,
        'livros': Livro.objects.all()
    })