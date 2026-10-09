from reportlab.pdfgen import canvas

# 1. Cria o arquivo PDF chamado 'nota_teste.pdf'
pdf = canvas.Canvas("nota_teste.pdf")

# 2. Escreve um texto simples dentro dele
pdf.drawString(100, 750, "Nota Fiscal #001 - Cliente: PyBuddy - Valor: R$ 1500,00")

# 3. Salva o arquivo na pasta
pdf.save()

print("PDF de teste criado com sucesso!")