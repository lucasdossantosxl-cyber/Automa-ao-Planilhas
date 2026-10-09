from pypdf import PdfReader

# 1. Carrega o PDF que acabamos de gerar
reader = PdfReader("nota_teste.pdf")

# 2. Pega a primeira página (em Python, a contagem começa em 0)
pagina = reader.pages[0]

# 3. Extrai o texto contido nela
texto = pagina.extract_text()

if not texto:
	raise ValueError("O PDF não contém texto extraível.")

marcador_valor = "Valor: "
if marcador_valor not in texto:
	raise ValueError(f'O campo "{marcador_valor.strip()}" não foi encontrado no PDF.')

valor_nota = texto.partition(marcador_valor)[2].splitlines()[0].strip()

# 3. Imprime apenas o valor extraído
print(valor_nota)

# 4. Exibe o texto lido no terminal
print(texto)