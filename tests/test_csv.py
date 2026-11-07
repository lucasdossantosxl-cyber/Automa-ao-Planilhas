from decimal import Decimal
from zipfile import ZipFile

import pytest

from consolidar import consolidar_vendas
from faturamento import calcular_total


@pytest.mark.parametrize(
    "linhas",
    [
        "Mouse,1,10,00\n",
        "Mouse,1,10.00\nTeclado,1,20,00\n",
        "Mouse,1\n",
        "Mouse,1,10.00\nTeclado,2\n",
    ],
)
def test_rejeita_csv_com_campos_faltantes_ou_extras(tmp_path, linhas):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    (entrada / "loja.csv").write_text(
        "Produto,Vendas,Preco\n" + linhas, encoding="utf-8"
    )
    destino = tmp_path / "relatorio.csv"
    with pytest.raises(ValueError, match="campos CSV"):
        consolidar_vendas(destino, entrada)
    assert not destino.exists()


def test_rejeita_csv_com_coluna_de_preco_duplicada(tmp_path):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    (entrada / "loja.csv").write_text(
        "Produto,Vendas,Preco,Preco\nMouse,1,10.00,100.00\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="duplicadas"):
        consolidar_vendas(tmp_path / "relatorio.csv", entrada)


def test_csv_com_bom_linhas_vazias_e_campo_entre_aspas(tmp_path):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    (entrada / "loja.csv").write_text(
        '\nProduto,Vendas,Preco\n\n"Mouse, modelo A\ngamer",2,"1.000,50"\n\n',
        encoding="utf-8-sig",
    )
    destino = consolidar_vendas(tmp_path / "relatorio.csv", entrada)
    assert calcular_total(destino) == Decimal("2001.00")


@pytest.mark.parametrize(
    "conteudo", ["", "\n\n", 'Produto,Vendas,Preco\n"Mouse,1,10\n']
)
def test_rejeita_csv_vazio_ou_com_aspas_incompletas(tmp_path, conteudo):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    (entrada / "loja.csv").write_text(conteudo, encoding="utf-8")
    with pytest.raises(ValueError, match="CSV inválido ou vazio"):
        consolidar_vendas(tmp_path / "relatorio.csv", entrada)


@pytest.mark.parametrize("zip_valido", [False, True])
def test_rejeita_xlsx_corrompido_ou_sem_planilha(tmp_path, zip_valido):
    entrada = tmp_path / "entrada"
    entrada.mkdir()
    origem = entrada / "loja.xlsx"
    if zip_valido:
        with ZipFile(origem, "w") as arquivo:
            arquivo.writestr("arquivo.txt", "Não contém um workbook.")
    else:
        origem.write_text("Não é um arquivo Excel.", encoding="utf-8")
    destino = tmp_path / "relatorio.csv"
    with pytest.raises(ValueError, match="loja.xlsx"):
        consolidar_vendas(destino, entrada)
    assert not destino.exists()
