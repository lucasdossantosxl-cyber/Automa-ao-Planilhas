import pandas as pd

# 1. Carrega o arquivo CSV para a memória
df = pd.read_csv("relatorio_final.csv")
# 2. Soma todos os valores da coluna 'Vendas'
total_vendas = df["Vendas"].sum()

# 3. Exibe o resultado formatado
print(f"Total geral de vendas: {total_vendas}")