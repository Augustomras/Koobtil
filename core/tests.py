from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Livro, Perfil

User = get_user_model()


class PaginasPublicasTests(TestCase):
    def test_landing_e_paginas_legais(self):
        for nome in ('core:landing', 'core:termos', 'core:privacidade', 'core:cadastro', 'login'):
            resp = self.client.get(reverse(nome))
            self.assertEqual(resp.status_code, 200, nome)

    def test_area_logada_exige_login(self):
        resp = self.client.get(reverse('core:home'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('login'), resp['Location'])


class FluxoAutenticadoTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ana', 'ana@example.com', 'senha-forte-123')
        Perfil.objects.create(usuario=self.user, nome_completo='Ana')
        self.livro = Livro.objects.create(
            titulo='Dom Casmurro', autor='Machado de Assis',
            pais_origem='Brasil', descricao='Clássico.',
        )
        self.client.force_login(self.user)

    def test_paginas_principais(self):
        for nome in ('core:home', 'core:explorar', 'core:perfil'):
            self.assertEqual(self.client.get(reverse(nome)).status_code, 200, nome)
        resp = self.client.get(reverse('core:detalhe_livro', args=[self.livro.id]))
        self.assertEqual(resp.status_code, 200)

    def test_favoritar_exige_post(self):
        url = reverse('core:favoritar_livro', args=[self.livro.id])
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)
        self.assertIn(self.livro, self.user.perfil.livros_favoritos.all())

    def test_busca(self):
        resp = self.client.get(reverse('core:buscar'), {'q': 'Dom'})
        self.assertContains(resp, 'Dom Casmurro')

    def test_usuario_comum_nao_exclui_livro(self):
        self.client.post(reverse('core:excluir_livro', args=[self.livro.id]))
        self.assertTrue(Livro.objects.filter(id=self.livro.id).exists())
