"""Ponto de entrada: python -m concertos <comando>."""

import argparse

from . import consultar, enriquecer, importar, site


def main():
    parser = argparse.ArgumentParser(
        prog="concertos",
        description="Organizador de espetáculos: importa os eventos do monitor "
        "de alertas, enriquece-os com datas e locais, e permite consultá-los.",
    )
    comandos = parser.add_subparsers(dest="comando", required=True)

    p_importar = comandos.add_parser(
        "importar", help="Importa o snapshot do monitor (ficheiro local ou URL)."
    )
    p_importar.add_argument(
        "origem", nargs="?", default=None,
        help="Caminho ou URL do eventos_oficiais_vistos.json "
        "(por omissão, o raw do GitHub de alertas-concertos-portugal).",
    )
    p_importar.set_defaults(executar=importar.executar)

    p_enriquecer = comandos.add_parser(
        "enriquecer", help="Visita as páginas dos eventos e extrai data, sala, artista."
    )
    p_enriquecer.add_argument("--limite", type=int, default=40,
                              help="Máximo de páginas a visitar (0 = sem limite).")
    p_enriquecer.add_argument("--forcar", action="store_true",
                              help="Tenta mesmo os eventos que já esgotaram as tentativas.")
    p_enriquecer.set_defaults(executar=enriquecer.executar)

    p_consultar = comandos.add_parser("consultar", help="Consulta os espetáculos.")
    p_consultar.add_argument("--artista", help="Filtra por artista ou título.")
    p_consultar.add_argument("--local", help="Filtra por sala ou fonte.")
    p_consultar.add_argument("--cidade", help="Filtra por cidade.")
    p_consultar.add_argument("--categoria",
                             help="música, teatro, dança, ballet, ópera, clássica, festival…")
    p_consultar.add_argument("--fonte", help="Filtra pela fonte do monitor.")
    p_consultar.add_argument("--texto", help="Pesquisa livre em todos os campos.")
    p_consultar.add_argument("--mes", help="Mês em formato 2026-09.")
    p_consultar.add_argument("--de", help="Data mínima (2026-09-01).")
    p_consultar.add_argument("--ate", help="Data máxima (2026-12-31).")
    p_consultar.add_argument("--sem-data", action="store_true", dest="sem_data",
                             help="Só eventos ainda sem data confirmada.")
    p_consultar.add_argument("--passados", action="store_true",
                             help="Inclui espetáculos com data já passada (arquivo).")
    p_consultar.add_argument("--todos", action="store_true",
                             help="Inclui eventos inativos (histórico).")
    p_consultar.add_argument("--json", action="store_true", help="Resultado em JSON.")
    p_consultar.set_defaults(executar=consultar.executar)

    p_site = comandos.add_parser("site", help="Gera o site estático de consulta (docs/index.html).")
    p_site.set_defaults(executar=site.executar)

    argumentos = parser.parse_args()
    argumentos.executar(argumentos)


if __name__ == "__main__":
    main()
