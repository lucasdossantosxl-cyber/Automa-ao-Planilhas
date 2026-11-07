# Automação de planilhas

Projeto de estudo em Python que transforma arquivos de vendas em um relatório consolidado, calcula o faturamento, gera um PDF e confere o valor extraído dele. O envio por e-mail é opcional.

```text
entrada/*.csv ou *.xlsx
    → consolidar vendas e identificar a filial
    → calcular quantidade × preço com Decimal
    → gerar PDF com o total
    → ler o PDF e conferir o valor
    → enviar o PDF por e-mail, se solicitado
```

O PDF é um relatório demonstrativo, sem validade fiscal. Os arquivos de exemplo contêm dados fictícios.

## Instalação

Requer **Python 3.10 ou superior**. Execute os comandos na pasta do repositório.

No Windows, com PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

No Linux ou macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

As dependências têm versões fixadas em `requirements.txt`.

## Executar a automação

```bash
python main.py
```

Por padrão, o programa lê `entrada/` e gera:

- `saida/relatorio_final.csv`, com as vendas de todas as filiais;
- `saida/nota.pdf`, com o faturamento total.

Os dois arquivos de exemplo produzem o total **R$ 30.285,00**. Executar sem opções gera e verifica os relatórios; o envio de e-mail exige `--enviar-email`.

Para usar outras pastas:

```bash
python main.py --entrada caminho/para/planilhas --saida caminho/para/relatorios
```

Os caminhos padrão são relativos ao local de `main.py`, permitindo executar o script de outro diretório. Os caminhos informados nas opções são relativos ao diretório atual, ou podem ser absolutos.

O programa registra as etapas com `logging` e retorna código `0` quando conclui, ou `1` quando encontra uma falha tratada.

## Formato dos arquivos de entrada

Coloque arquivos `.csv` ou `.xlsx` diretamente em `entrada/`. Para XLSX, somente a primeira aba é lida. Cada arquivo precisa conter estas colunas:

| Coluna | Conteúdo |
| --- | --- |
| `Produto` | Nome não vazio; espaços externos são removidos e a capitalização é padronizada. |
| `Vendas` | Quantidade inteira não negativa. |
| `Preco` | Preço unitário não negativo, em reais, com precisão de centavos. |

Exemplo de `entrada/filial_a.csv`:

```csv
Produto,Vendas,Preco
Notebook,5,3500.00
Mouse,12,80.00
Teclado,8,150.00
```

CSV aceita vírgula ou ponto e vírgula como separador. Para preços no formato brasileiro, use ponto e vírgula ou coloque o preço entre aspas:

```csv
Produto;Vendas;Preco
Headset;2;200,00
Monitor;1;1.500,25
```

```csv
Produto,Vendas,Preco
Monitor,1,"1.500,25"
```

O nome do arquivo, sem a extensão, vira a coluna `Filial`: `filial_a.csv` identifica `filial_a`. Use nomes distintos para arquivos de filiais diferentes. O consolidado inclui `Filial`, `Produto`, `Vendas`, `Preco` e `Faturamento`; os valores monetários são gravados com ponto decimal.

O faturamento de cada linha é `Vendas × Preco`, calculado com `Decimal`. Entradas vazias, colunas obrigatórias ausentes, quantidades fracionárias ou negativas e preços inválidos são rejeitados. Se existir uma coluna `Faturamento` na entrada, ela precisa coincidir com o subtotal calculado.

## Configurar o e-mail

Copie `.env.example` para `.env` e preencha os dados localmente.

PowerShell:

```powershell
Copy-Item .env.example .env
```

Linux ou macOS:

```bash
cp .env.example .env
```

| Variável | Uso |
| --- | --- |
| `SMTP_USER` | Usuário para autenticação SMTP; obrigatório para enviar. |
| `SMTP_PASSWORD` | Senha ou senha de aplicativo; obrigatória para enviar. |
| `EMAIL_TO` | Destinatário; obrigatório para enviar. |
| `SMTP_HOST` | Servidor SMTP; padrão `smtp.gmail.com`. |
| `SMTP_PORT` | Porta SMTP; padrão `587`. |
| `EMAIL_FROM` | Remetente; usa `SMTP_USER` se estiver vazio ou ausente. |
| `SMTP_TIMEOUT` | Tempo limite positivo, em segundos; padrão `30`. |

O programa carrega o `.env` ao lado de `main.py`, sem substituir variáveis já definidas no ambiente. Os padrões de servidor, porta e timeout são usados quando essas variáveis estão ausentes; o arquivo de exemplo já contém os valores padrão.

Depois de configurar:

```bash
python main.py --enviar-email
```

O envio usa SMTP com **STARTTLS**, normalmente na porta **587**, com verificação de certificado. O e-mail contém o total conferido e o PDF em anexo. Para Gmail, utilize uma senha de aplicativo quando aplicável à sua conta.

Não publique credenciais. O `.env`, os relatórios gerados e a pasta de ambiente virtual ficam fora do Git; `.env.example` contém apenas exemplos e campos vazios para as credenciais.

## Qualidade e testes

Com o ambiente virtual ativo:

```bash
python -m pip install -r requirements-dev.txt
ruff format --check .
ruff check .
python -m pytest -q
```

Para aplicar a formatação, execute `ruff format .`.

Os testes verificam a conversão monetária, consolidação CSV/XLSX, validação das entradas, geração e extração do PDF e o fluxo completo. As verificações de e-mail usam simulações de SMTP, sem envio real e sem necessidade de credenciais.

O GitHub Actions executa a formatação, o lint e o pytest a cada push e pull request, em Python **3.10** e **3.12**.

## Organização

| Arquivo ou pasta | Responsabilidade |
| --- | --- |
| `main.py` | Interface de linha de comando e sequência da automação. |
| `consolidar.py` | Leitura, validação e consolidação das planilhas. |
| `dinheiro.py` | Conversão e formatação dos valores monetários. |
| `faturamento.py` | Cálculo e conferência do total. |
| `gerar_pdf.py` | Geração do relatório PDF. |
| `leitor_pdf.py` | Extração do valor do relatório. |
| `enviar_email.py` | Configuração SMTP e envio opcional. |
| `entrada/` | Arquivos fictícios para experimentar o fluxo. |
| `tests/` | Testes automatizados. |
