import pandas as pd

# 1. Dados da Filial A
dados_filial_a = {
    "Produto": ["Notebook", "Mouse", "Teclado"],
    "Vendas": [5, 12, 8]
}
df_a = pd.DataFrame(dados_filial_a)

# 2. Dados da Filial B
dados_filial_b = {
    "Produto": ["headset", "Monitor", "Cabo"],
    "Vendas": [19, 7, 21]
}
df_b = pd.DataFrame(dados_filial_b)

# 3. Consolidação das duas tabelas
df_consolidado = pd.concat([df_a, df_b], ignore_index=True)

# 4. Exibição apenas da tabela consolidada
print(df_consolidado)
# Exemplo de salvamento em CSV:
df_consolidado.to_csv("relatorio_final.csv", index=False)
