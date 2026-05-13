from django.contrib import admin
from .models import Eleitor, Eleicao, Candidato, AptidaoEleitor, RegistroVotacao, Voto

# Register your models here.

@admin.register(Eleitor)
class EleitorAdmin(admin.ModelAdmin):
    pass


@admin.register(Eleicao)
class EleicaoAdmin(admin.ModelAdmin):
    pass


@admin.register(Candidato)
class CandidatoAdmin(admin.ModelAdmin):
    pass


@admin.register(AptidaoEleitor)
class AptidaoEleitorAdmin(admin.ModelAdmin):
    pass


@admin.register(RegistroVotacao)
class RegistroVotacaoAdmin(admin.ModelAdmin):
    pass


@admin.register(Voto)
class VotoAdmin(admin.ModelAdmin):
    pass