import json
import csv
import os
import hashlib
from datetime import datetime


# =========================
# Configurações
# =========================

ARQUIVO_EXPORT = "gastos_export.csv"
ARQUIVO_USUARIOS = "usuarios.json"


def arquivo_dados_do_usuario(usuario):
    return f"gastos_{usuario}.json"


# =========================
# Usuários (login/cadastro)
# =========================

def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def carregar_usuarios():
    try:
        with open(ARQUIVO_USUARIOS, "r", encoding="utf-8") as f:
            dados = json.load(f)
            return dados if isinstance(dados, dict) else {}
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print("\n⚠️ usuarios.json corrompido. Criando novo.")
        return {}


def salvar_usuarios(usuarios):
    with open(ARQUIVO_USUARIOS, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, ensure_ascii=False, indent=2)


def nome_usuario_valido(usuario):
    usuario = usuario.strip()
    if len(usuario) < 3:
        return False
    for ch in usuario:
        if not (ch.isalnum() or ch in "_-"):
            return False
    return True


def cadastrar_usuario():
    usuarios = carregar_usuarios()

    limpar_tela()
    print("=== CADASTRO ===\n")

    while True:
        usuario = input("Novo usuário (mín. 3 chars, letras/números/_/-): ").strip()

        if not nome_usuario_valido(usuario):
            print("Usuário inválido.")
            continue

        if usuario in usuarios:
            print("Esse usuário já existe.")
            continue

        break

    while True:
        senha = input("Senha (mín. 4): ").strip()
        if len(senha) < 4:
            print("Senha muito curta.")
            continue

        senha2 = input("Confirmar senha: ").strip()
        if senha != senha2:
            print("Senhas não batem.")
            continue

        break

    usuarios[usuario] = {"senha_hash": hash_senha(senha)}
    salvar_usuarios(usuarios)

    print("\n✅ Usuário criado com sucesso!")
    pausar()
    return usuario


def autenticar_usuario():
    usuarios = carregar_usuarios()

    limpar_tela()
    print("=== ENTRAR ===\n")

    usuario = input("Usuário: ").strip()
    senha = input("Senha: ").strip()

    registro = usuarios.get(usuario)

    if not registro:
        print("\nUsuário não encontrado.")
        pausar()
        return None

    if registro.get("senha_hash") != hash_senha(senha):
        print("\nSenha incorreta.")
        pausar()
        return None

    print("\n✅ Login realizado!")
    pausar()
    return usuario


def menu_autenticacao():
    while True:
        limpar_tela()
        print("-" * 44)
        print("   GERENCIADOR DE GASTOS (CLI)  💸")
        print("-" * 44)

        print("\n1 - Entrar")
        print("2 - Cadastrar")
        print("0 - Sair")

        op = input("\n> ").strip()

        if op == "1":
            usuario = autenticar_usuario()
            if usuario:
                return usuario

        elif op == "2":
            usuario = cadastrar_usuario()
            if usuario:
                return usuario

        elif op == "0":
            print("\nEncerrando...")
            return None

        else:
            print("\nOpção inválida.")
            pausar()


# =========================
# Arquivos (JSON) - por usuário
# =========================

def salvar_gastos(gastos, usuario):
    caminho = arquivo_dados_do_usuario(usuario)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(gastos, arquivo, ensure_ascii=False, indent=2)


def carregar_gastos(usuario):
    caminho = arquivo_dados_do_usuario(usuario)
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
            return dados if isinstance(dados, list) else []
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print("\n⚠️ O arquivo JSON do usuário está corrompido. Iniciando lista vazia.")
        return []


# =========================
# UX (terminal)
# =========================

def limpar_tela():
    os.system("cls" if os.name == "nt" else "clear")


def pausar():
    input("\nPressione Enter para continuar...")


def perguntar_voltar_ou_encerrar(gastos, usuario):
    while True:
        resp = input("\nVoltar ao menu? (Sim/Não): ").strip().lower()

        resp = (
            resp.replace("ã", "a").replace("á", "a").replace("â", "a").replace("à", "a")
                .replace("õ", "o").replace("ó", "o").replace("ô", "o").replace("ò", "o")
        )

        if resp in ("s", "sim", "y", "yes"):
            return True

        if resp in ("n", "nao", "no"):
            salvar_gastos(gastos, usuario)
            print("\nEncerrando...")
            return False

        print("Responda com Sim ou Não.")


# =====================
# Validações e Inputs
# =====================

def pedir_float_positivo(msg):
    while True:
        try:
            valor = float(input(msg).replace(",", "."))
            if valor <= 0:
                print("Digite um valor maior que zero.")
            else:
                return valor
        except ValueError:
            print("Digite um número válido. Ex: 12.50")


def validar_data_yyyy_mm_dd(texto):
    try:
        datetime.strptime(texto, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def pedir_data_opcional():
    while True:
        data = input("Data (YYYY-MM-DD) ou Enter para pular: ").strip()
        if data == "":
            return None
        if validar_data_yyyy_mm_dd(data):
            return data
        print("Formato inválido. Exemplo: 2026-02-08")


def pedir_data_obrigatoria(msg):
    while True:
        data = input(msg).strip()
        if validar_data_yyyy_mm_dd(data):
            return data
        print("Formato inválido. Exemplo: 2026-02-08")


def pedir_indice_gasto(total):
    while True:
        try:
            escolha = int(input(f"\nDigite o número do gasto (1 a {total}) ou 0 para cancelar: "))
            if escolha == 0:
                return None
            if 1 <= escolha <= total:
                return escolha - 1
            print("Número fora do intervalo.")
        except ValueError:
            print("Digite um número inteiro válido.")


def normalizar_texto(s):
    s = (s or "").strip().lower()
    s = (
        s.replace("ã", "a").replace("á", "a").replace("â", "a").replace("à", "a")
         .replace("õ", "o").replace("ó", "o").replace("ô", "o").replace("ò", "o")
         .replace("ç", "c")
    )
    return s


# =====================
# Listagem e filtros
# =====================

def formatar_gasto(i, gasto):
    data = gasto.get("data")
    data_txt = data if isinstance(data, str) and data else "sem data"
    return (
        f"{i}) "
        f"Data: {data_txt} | "
        f"Descrição: {gasto.get('descricao', '')} | "
        f"Categoria: {gasto.get('categoria', '')} | "
        f"Valor: R$ {float(gasto.get('valor', 0)):.2f}"
    )


def listar_gastos(gastos):
    print("\n=== LISTA DE GASTOS ===")

    if not gastos:
        print("Nenhum gasto registrado.")
        return

    for i, gasto in enumerate(gastos, start=1):
        print(formatar_gasto(i, gasto))


def filtrar_por_mes(gastos, yyyy_mm):
    filtrados = []
    for g in gastos:
        data = g.get("data")
        if isinstance(data, str) and len(data) >= 7 and data[:7] == yyyy_mm:
            filtrados.append(g)
    return filtrados


def filtrar_por_intervalo(gastos, data_ini, data_fim):
    dt_ini = datetime.strptime(data_ini, "%Y-%m-%d").date()
    dt_fim = datetime.strptime(data_fim, "%Y-%m-%d").date()

    filtrados = []
    for g in gastos:
        data = g.get("data")
        if not (isinstance(data, str) and validar_data_yyyy_mm_dd(data)):
            continue
        dt = datetime.strptime(data, "%Y-%m-%d").date()
        if dt_ini <= dt <= dt_fim:
            filtrados.append(g)
    return filtrados


def buscar_gastos(gastos, termo=None, categoria=None):
    termo_n = normalizar_texto(termo) if termo else None
    cat_n = normalizar_texto(categoria) if categoria else None

    achados = []
    for g in gastos:
        desc_n = normalizar_texto(g.get("descricao", ""))
        catg_n = normalizar_texto(g.get("categoria", ""))

        ok = True

        if termo_n:
            ok = termo_n in desc_n

        if ok and cat_n:
            ok = cat_n == catg_n

        if ok:
            achados.append(g)

    return achados


def ordenar_gastos(gastos, chave, reverso=False):
    def chave_sort(g):
        if chave == "valor":
            return float(g.get("valor", 0))
        if chave == "data":
            data = g.get("data")
            if isinstance(data, str) and validar_data_yyyy_mm_dd(data):
                return datetime.strptime(data, "%Y-%m-%d")
            return datetime.max
        if chave == "categoria":
            return normalizar_texto(g.get("categoria", ""))
        if chave == "descricao":
            return normalizar_texto(g.get("descricao", ""))
        return 0

    return sorted(gastos, key=chave_sort, reverse=reverso)


# ===========
# Resumos
# ===========

def resumo_por_categoria(gastos):
    resumo = {}
    for g in gastos:
        cat = g.get("categoria", "Sem categoria")
        val = float(g.get("valor", 0))
        resumo[cat] = resumo.get(cat, 0.0) + val
    return resumo


def mostrar_resumo(gastos, titulo="Resumo"):
    print(f"\n=== {titulo} ===")

    if not gastos:
        print("Nenhum gasto encontrado.")
        return

    total = sum(float(g.get("valor", 0)) for g in gastos)
    media = total / len(gastos) if gastos else 0

    print(f"\nQuantidade de gastos: {len(gastos)}")
    print(f"Total geral: R$ {total:.2f}")
    print(f"Média por gasto: R$ {media:.2f}")

    resumo = resumo_por_categoria(gastos)
    print("\nTotal por categoria:")

    top = sorted(resumo.items(), key=lambda x: x[1], reverse=True)

    for cat, val in top:
        print(f"- {cat}: R$ {val:.2f}")

    print("\nTop 3 categorias:")
    for i, (cat, val) in enumerate(top[:3], start=1):
        print(f"{i}) {cat} — R$ {val:.2f}")


# ==============
# Export (CSV)
# ==============

def exportar_csv(gastos, caminho=ARQUIVO_EXPORT):
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["data", "descricao", "categoria", "valor"])

        for g in gastos:
            writer.writerow([
                g.get("data") or "",
                g.get("descricao") or "",
                g.get("categoria") or "",
                f"{float(g.get('valor', 0)):.2f}"
            ])


# =========
# CRUD
# =========

def adicionar_gasto(gastos, usuario):
    limpar_tela()
    print("=== ADICIONAR GASTO ===\n")

    descricao = input("Descrição: ").strip()
    categoria = input("Categoria: ").strip()
    valor = pedir_float_positivo("Valor (R$): ")
    data = pedir_data_opcional()

    gasto = {
        "descricao": descricao,
        "categoria": categoria,
        "valor": valor,
        "data": data
    }

    gastos.append(gasto)
    salvar_gastos(gastos, usuario)

    print("\n✅ Gasto registrado com sucesso!")
    print(formatar_gasto(len(gastos), gasto))


def editar_gasto(gastos, usuario):
    limpar_tela()
    print("=== EDITAR GASTO ===")

    if not gastos:
        print("\nNenhum gasto para editar.")
        return

    listar_gastos(gastos)

    idx = pedir_indice_gasto(len(gastos))
    if idx is None:
        print("\nEdição cancelada.")
        return

    g = gastos[idx]
    print("\nGasto selecionado:")
    print(formatar_gasto(idx + 1, g))

    print("\nO que deseja editar?")
    print("1 - Descrição")
    print("2 - Categoria")
    print("3 - Valor")
    print("4 - Data")
    print("0 - Cancelar")

    escolha = input("\n> ").strip()

    if escolha == "1":
        novo = input("Nova descrição: ").strip()
        if novo:
            g["descricao"] = novo

    elif escolha == "2":
        novo = input("Nova categoria: ").strip()
        if novo:
            g["categoria"] = novo

    elif escolha == "3":
        g["valor"] = pedir_float_positivo("Novo valor (R$): ")

    elif escolha == "4":
        g["data"] = pedir_data_opcional()

    elif escolha == "0":
        print("\nEdição cancelada.")
        return

    else:
        print("\nOpção inválida.")
        return

    salvar_gastos(gastos, usuario)
    print("\n✅ Gasto atualizado:")
    print(formatar_gasto(idx + 1, g))


def remover_gasto(gastos, usuario):
    limpar_tela()
    print("=== REMOVER GASTO ===")

    if not gastos:
        print("\nNenhum gasto para remover.")
        return

    listar_gastos(gastos)

    idx = pedir_indice_gasto(len(gastos))
    if idx is None:
        print("\nRemoção cancelada.")
        return

    removido = gastos.pop(idx)
    salvar_gastos(gastos, usuario)

    print("\n✅ Gasto removido:")
    print(
        f"Data: {(removido.get('data') or 'sem data')} | "
        f"Descrição: {removido.get('descricao', '')} | "
        f"Categoria: {removido.get('categoria', '')} | "
        f"Valor: R$ {float(removido.get('valor', 0)):.2f}"
    )


# ====================
# Menus
# ====================

def menu_dados(gastos, usuario):
    while True:
        limpar_tela()
        print("=== DADOS (Salvar / Carregar / Limpar) ===\n")
        print("1 - Salvar agora")
        print("2 - Recarregar do arquivo")
        print("3 - Limpar todos os dados")
        print("0 - Voltar")

        op = input("\n> ").strip()

        if op == "1":
            salvar_gastos(gastos, usuario)
            print("\n✅ Dados salvos.")
            pausar()

        elif op == "2":
            novos = carregar_gastos(usuario)
            gastos.clear()
            gastos.extend(novos)
            print("\n✅ Dados recarregados do arquivo.")
            pausar()

        elif op == "3":
            conf = input("\nTem certeza? (digite APAGAR para confirmar): ").strip()
            if conf == "APAGAR":
                gastos.clear()
                salvar_gastos(gastos, usuario)
                print("\n✅ Tudo apagado.")
            else:
                print("\nCancelado.")
            pausar()

        elif op == "0":
            return

        else:
            print("\nOpção inválida.")
            pausar()


def menu_listagem(gastos):
    while True:
        limpar_tela()
        print("=== LISTAGEM / FILTROS / ORDENAR ===\n")
        print("1 - Listar tudo")
        print("2 - Listar por mês (YYYY-MM)")
        print("3 - Listar por intervalo de datas (YYYY-MM-DD)")
        print("4 - Ordenar (data/valor/categoria/descricao)")
        print("0 - Voltar")

        op = input("\n> ").strip()

        if op == "1":
            limpar_tela()
            listar_gastos(gastos)
            pausar()

        elif op == "2":
            mes = input("\nMês (YYYY-MM): ").strip()
            filtrados = filtrar_por_mes(gastos, mes)
            limpar_tela()
            listar_gastos(filtrados)
            pausar()

        elif op == "3":
            di = pedir_data_obrigatoria("\nData inicial (YYYY-MM-DD): ")
            df = pedir_data_obrigatoria("Data final (YYYY-MM-DD): ")
            filtrados = filtrar_por_intervalo(gastos, di, df)
            limpar_tela()
            listar_gastos(filtrados)
            pausar()

        elif op == "4":
            chave = input("\nOrdenar por (data/valor/categoria/descricao): ").strip().lower()
            if chave not in ("data", "valor", "categoria", "descricao"):
                print("Chave inválida.")
                pausar()
                continue

            sentido = input("Ordem (cresc/desc): ").strip().lower()
            reverso = (sentido == "desc")

            ordenados = ordenar_gastos(gastos, chave, reverso=reverso)

            limpar_tela()
            listar_gastos(ordenados)
            pausar()

        elif op == "0":
            return

        else:
            print("\nOpção inválida.")
            pausar()


def menu_busca(gastos):
    while True:
        limpar_tela()
        print("=== BUSCA ===\n")
        print("1 - Buscar por palavra na descrição")
        print("2 - Buscar por categoria")
        print("3 - Buscar por palavra + categoria")
        print("0 - Voltar")

        op = input("\n> ").strip()

        if op == "1":
            termo = input("\nPalavra (descrição): ").strip()
            achados = buscar_gastos(gastos, termo=termo)
            limpar_tela()
            listar_gastos(achados)
            mostrar_resumo(achados, titulo="Resumo da busca")
            pausar()

        elif op == "2":
            cat = input("\nCategoria: ").strip()
            achados = buscar_gastos(gastos, categoria=cat)
            limpar_tela()
            listar_gastos(achados)
            mostrar_resumo(achados, titulo="Resumo da busca")
            pausar()

        elif op == "3":
            termo = input("\nPalavra (descrição): ").strip()
            cat = input("Categoria: ").strip()
            achados = buscar_gastos(gastos, termo=termo, categoria=cat)
            limpar_tela()
            listar_gastos(achados)
            mostrar_resumo(achados, titulo="Resumo da busca")
            pausar()

        elif op == "0":
            return

        else:
            print("\nOpção inválida.")
            pausar()


def menu_resumo(gastos):
    while True:
        limpar_tela()
        print("=== RESUMOS ===\n")
        print("1 - Resumo geral")
        print("2 - Resumo por mês (YYYY-MM)")
        print("3 - Resumo por intervalo de datas (YYYY-MM-DD)")
        print("0 - Voltar")

        op = input("\n> ").strip()

        if op == "1":
            limpar_tela()
            mostrar_resumo(gastos, titulo="Resumo geral")
            pausar()

        elif op == "2":
            mes = input("\nMês (YYYY-MM): ").strip()
            filtrados = filtrar_por_mes(gastos, mes)
            limpar_tela()
            mostrar_resumo(filtrados, titulo=f"Resumo do mês {mes}")
            pausar()

        elif op == "3":
            di = pedir_data_obrigatoria("\nData inicial (YYYY-MM-DD): ")
            df = pedir_data_obrigatoria("Data final (YYYY-MM-DD): ")
            filtrados = filtrar_por_intervalo(gastos, di, df)
            limpar_tela()
            mostrar_resumo(filtrados, titulo=f"Resumo {di} até {df}")
            pausar()

        elif op == "0":
            return

        else:
            print("\nOpção inválida.")
            pausar()


def menu_exportar(gastos):
    while True:
        limpar_tela()
        print("=== EXPORTAR CSV ===\n")
        print(f"Arquivo padrão: {ARQUIVO_EXPORT}\n")
        print("1 - Exportar tudo")
        print("2 - Exportar por mês (YYYY-MM)")
        print("3 - Exportar por intervalo de datas (YYYY-MM-DD)")
        print("0 - Voltar")

        op = input("\n> ").strip()

        if op == "1":
            exportar_csv(gastos, ARQUIVO_EXPORT)
            print(f"\n✅ Exportado para {ARQUIVO_EXPORT}")
            pausar()

        elif op == "2":
            mes = input("\nMês (YYYY-MM): ").strip()
            filtrados = filtrar_por_mes(gastos, mes)
            nome = f"gastos_{mes}.csv"
            exportar_csv(filtrados, nome)
            print(f"\n✅ Exportado para {nome}")
            pausar()

        elif op == "3":
            di = pedir_data_obrigatoria("\nData inicial (YYYY-MM-DD): ")
            df = pedir_data_obrigatoria("Data final (YYYY-MM-DD): ")
            filtrados = filtrar_por_intervalo(gastos, di, df)
            nome = f"gastos_{di}_ate_{df}.csv".replace("-", "")
            nome = f"{nome}.csv"
            exportar_csv(filtrados, nome)
            print(f"\n✅ Exportado para {nome}")
            pausar()

        elif op == "0":
            return

        else:
            print("\nOpção inválida.")
            pausar()


# ===================
# App
# ===================

def main():
    usuario = menu_autenticacao()
    if usuario is None:
        return

    gastos = carregar_gastos(usuario)

    while True:
        limpar_tela()

        print("-" * 44)
        print(f"   GERENCIADOR DE GASTOS (CLI)  💸   [{usuario}]")
        print("-" * 44)

        print("\n1 - Adicionar gasto")
        print("2 - Editar gasto")
        print("3 - Remover gasto")

        print("\n4 - Listagem / Filtros / Ordenar")
        print("5 - Busca")
        print("6 - Resumos")
        print("7 - Exportar CSV")
        print("8 - Dados (Salvar / Carregar / Limpar)")

        print("\nDigite 'sair' para encerrar")

        opcao = input("\n> ").strip().lower()

        if opcao == "1":
            adicionar_gasto(gastos, usuario)
            if not perguntar_voltar_ou_encerrar(gastos, usuario):
                break

        elif opcao == "2":
            editar_gasto(gastos, usuario)
            pausar()
            if not perguntar_voltar_ou_encerrar(gastos, usuario):
                break

        elif opcao == "3":
            remover_gasto(gastos, usuario)
            pausar()
            if not perguntar_voltar_ou_encerrar(gastos, usuario):
                break

        elif opcao == "4":
            menu_listagem(gastos)

        elif opcao == "5":
            menu_busca(gastos)

        elif opcao == "6":
            menu_resumo(gastos)

        elif opcao == "7":
            menu_exportar(gastos)

        elif opcao == "8":
            menu_dados(gastos, usuario)

        elif opcao == "sair":
            salvar_gastos(gastos, usuario)
            print("\nEncerrando...")
            break

        else:
            print("\nOpção inválida.")
            pausar()


if __name__ == "__main__":
    main()
