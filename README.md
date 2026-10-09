# Automa-ao-Planilhas

Projeto de estudo com exemplos independentes de automação em Python: consolidação de vendas em CSV, soma de faturamento, criação e leitura de PDF e envio de e-mail.

## Requisitos

- Python 3.10 ou superior

Instale as dependências com:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Executar os exemplos

Rode os comandos a partir desta pasta:

```powershell
python main.py
python faturamento.py
python gerar_pdf.py
python leitor_pdf.py
```

`main.py` cria `relatorio_final.csv`. `faturamento.py` lê esse CSV e mostra a soma das vendas. `gerar_pdf.py` cria `nota_teste.pdf`, que pode ser lido por `leitor_pdf.py`.

## Enviar e-mail

O envio usa variáveis de ambiente para não deixar credenciais no código. Configure-as na sessão atual do PowerShell:

```powershell
$env:SMTP_HOST = "smtp.gmail.com"
$env:SMTP_PORT = "587"
$env:SMTP_USER = "seu_email@gmail.com"
$env:SMTP_PASSWORD = "sua_senha_de_app"
$env:EMAIL_TO = "destinatario@example.com"
python enviar_email.py
```

Para Gmail, use uma senha de app quando a verificação em duas etapas estiver habilitada. Não publique senhas, tokens ou arquivos `.env`.

Os arquivos `relatorio_final.csv` e `nota_teste.pdf` são resultados gerados e ficam fora do Git por padrão.
