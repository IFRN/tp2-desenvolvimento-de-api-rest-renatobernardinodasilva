from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import PROTECT, CASCADE

class Eleitor(models.Model):
    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    cpf = models.CharField(max_length=14, unique=True)
    data_nascimento = models.DateField()
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

class Eleicao(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    tipo = models.CharField(max_length=20,choices=[
        ("estudantil", "Estudantil"),
        ("sindical", "Sindical"),
        ("associacao", "Associacao"),
        ("condominio", "Condominio"),
        ("conselho", "Conselho"),
        ("outra", "Outra"),
    ],)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    status = models.CharField(max_length=20,choices=[
        ("rascunho", "Rascunho"),
        ("aberta", "Aberta"),
        ("encerrada", "Encerrada"),
        ("apurada", "Apurada"),
    ],
    default="rascunho",
    )
    permite_branco = models.BooleanField(default=True)
    criada_por = models.ForeignKey(Eleitor, on_delete=PROTECT, related_name='eleicoes_criadas')
    
    def clean(self):
        if self.data_fim <= self.data_inicio:
            raise ValidationError("A data final deve ser maior que a data inicial.")

        if self.pk:
            antiga = Eleicao.objects.get(pk=self.pk)

            fluxo = {
                "rascunho": ["aberta"],
                "aberta": ["encerrada"],
                "encerrada": ["apurada"],
                "apurada": [],
            }

            if antiga.status != self.status:
                if self.status not in fluxo[antiga.status]:
                    raise ValidationError("Fluxo de status inválido.")
    def __str__(self):
        return self.titulo

class Candidato(models.Model):
    eleicao = models.ForeignKey(Eleicao, on_delete=CASCADE, related_name='candidatos')
    numero = models.PositiveIntegerField() 
    nome = models.CharField(max_length=150)
    nome_urna = models.CharField(max_length=50)
    partido_ou_chapa = models.CharField(max_length=100, blank = True)
    proposta = models.TextField(blank=True)
    foto_url = models.URLField(blank=True)
    
    class Meta:
        unique_together = [("eleicao", "numero")]

    def __str__(self):
        return self.nome_urna

class AptidaoEleitor(models.Model):
    eleitor= models.CharField(max_length=100)
    eleicao = models.ForeignKey(Eleicao, on_delete=CASCADE, related_name='aptos')
    data_inclusao = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [("eleitor", "eleicao")]

    def __str__(self):
        return f"{self.eleitor.nome} - {self.eleicao.titulo}"

class RegistroVotacao(models.Model):
    eleitor= models.ForeignKey(Eleitor, on_delete=PROTECT, related_name='registros_votacao')
    eleicao = models.ForeignKey(Eleicao, on_delete=PROTECT,related_name='registros_votacao')
    data_hora = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [("eleitor", "eleicao")]
    
    def __str__(self):
        return f"{self.eleitor.nome} - {self.eleicao.titulo}"

class Voto(models.Model):
    eleicao = models.ForeignKey(Eleicao, on_delete=PROTECT, related_name='votos')
    candidato = models.ForeignKey(Candidato, on_delete=PROTECT, related_name='votos', null=True, blank=True)
    em_branco = models.BooleanField(default=False)
    data_hora = models.DateTimeField(auto_now_add=True)
    comprovante_hash = models.CharField(max_length=64, unique=True) 
    
    def clean(self):
        if self.em_branco and self.candidato is not None:
            raise ValidationError(
                "Voto em branco não pode ter candidato."
            )

        if not self.em_branco and self.candidato is None:
            raise ValidationError(
                "Voto precisa ter um candidato."
            )

    def __str__(self):
        return f"Voto {self.id} - {self.eleicao.titulo}"