#!/usr/bin/env python3
"""Analisa perfis profissionais do Instagram via Business Discovery (Graph API).

Uso:
    python3 scripts/analisar_perfis.py --descobrir-id
    python3 scripts/analisar_perfis.py perfil1 perfil2 [--posts 30]

Precisa das variáveis IG_ACCESS_TOKEN e IG_USER_ID (ou de um arquivo .env).
Só funciona com contas profissionais (Criador de conteúdo ou Empresa).
Gera um relatório em analises/AAAA-MM-DD-<perfil>.md e os dados brutos em .json.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_SAIDA = RAIZ / "analises"

TIPOS = {"IMAGE": "Foto", "VIDEO": "Vídeo/Reels", "CAROUSEL_ALBUM": "Carrossel"}


def carregar_env():
    arquivo = RAIZ / ".env"
    if not arquivo.exists():
        return
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            chave, valor = linha.split("=", 1)
            os.environ.setdefault(chave.strip(), valor.strip())


def graph(caminho, params):
    versao = os.environ.get("GRAPH_API_VERSION", "v23.0")
    params = {**params, "access_token": os.environ["IG_ACCESS_TOKEN"]}
    url = f"https://graph.facebook.com/{versao}/{caminho}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as erro:
        detalhe = json.load(erro).get("error", {})
        raise RuntimeError(detalhe.get("message", str(erro))) from None


def descobrir_id():
    dados = graph("me/accounts", {"fields": "name,instagram_business_account{id,username}"})
    encontrou = False
    for pagina in dados.get("data", []):
        conta = pagina.get("instagram_business_account")
        if conta:
            encontrou = True
            print(f"Página '{pagina['name']}' -> @{conta['username']}  IG_USER_ID={conta['id']}")
    if not encontrou:
        print("Nenhuma conta do Instagram vinculada às suas Páginas. Revise o passo 2 do guia.")


def buscar_perfil(usuario, n_posts):
    campos_post = "caption,like_count,comments_count,timestamp,media_type,permalink"
    campos = (
        f"business_discovery.username({usuario})"
        f"{{username,name,biography,website,followers_count,follows_count,media_count,"
        f"media.limit({n_posts}){{{campos_post}}}}}"
    )
    dados = graph(os.environ["IG_USER_ID"], {"fields": campos})
    return dados["business_discovery"]


def engajamento(post):
    return (post.get("like_count") or 0) + (post.get("comments_count") or 0)


def resumo(texto, limite=90):
    texto = " ".join((texto or "").split())
    return texto if len(texto) <= limite else texto[: limite - 1] + "…"


def montar_relatorio(perfil):
    seguidores = perfil.get("followers_count") or 0
    posts = perfil.get("media", {}).get("data", [])
    taxa = lambda valor: f"{valor / seguidores * 100:.2f}%" if seguidores else "—"

    linhas = [
        f"# @{perfil['username']} — {perfil.get('name', '')}",
        "",
        f"_Coletado em {date.today():%d/%m/%Y} · últimos {len(posts)} posts_",
        "",
        f"**Bio:** {resumo(perfil.get('biography'), 300)}",
        f"**Link:** {perfil.get('website') or '—'}",
        "",
        "| Seguidores | Seguindo | Posts |",
        "|---|---|---|",
        f"| {seguidores:,} | {perfil.get('follows_count', 0):,} | {perfil.get('media_count', 0):,} |".replace(",", "."),
        "",
    ]
    if not posts:
        return "\n".join(linhas + ["Nenhum post retornado."])

    curtidas_ocultas = sum(1 for p in posts if "like_count" not in p)
    media_eng = sum(engajamento(p) for p in posts) / len(posts)
    datas = sorted(datetime.fromisoformat(p["timestamp"].replace("+0000", "+00:00")) for p in posts)
    semanas = max((datas[-1] - datas[0]).days / 7, 1)

    linhas += [
        "## Visão geral",
        "",
        f"- Engajamento médio por post: **{media_eng:.0f}** interações ({taxa(media_eng)} dos seguidores)",
        f"- Frequência: **{len(posts) / semanas:.1f} posts/semana** (de {datas[0]:%d/%m/%Y} a {datas[-1]:%d/%m/%Y})",
    ]
    if curtidas_ocultas:
        linhas.append(f"- ⚠️ {curtidas_ocultas} post(s) com curtidas ocultas — contam só comentários")
    linhas += ["", "## Por formato", "", "| Formato | Posts | Engajamento médio | Taxa |", "|---|---|---|---|"]

    por_tipo = defaultdict(list)
    for p in posts:
        por_tipo[p.get("media_type")].append(engajamento(p))
    for tipo, valores in sorted(por_tipo.items(), key=lambda kv: -sum(kv[1]) / len(kv[1])):
        media = sum(valores) / len(valores)
        linhas.append(f"| {TIPOS.get(tipo, tipo)} | {len(valores)} | {media:.0f} | {taxa(media)} |")

    linhas += ["", "## Top 5 posts", "", "| Data | Formato | Curtidas | Coment. | Legenda |", "|---|---|---|---|---|"]
    for p in sorted(posts, key=engajamento, reverse=True)[:5]:
        quando = p["timestamp"][:10]
        legenda = resumo(p.get("caption")).replace("|", "/")
        linhas.append(
            f"| [{quando}]({p['permalink']}) | {TIPOS.get(p.get('media_type'), p.get('media_type'))} "
            f"| {p.get('like_count', 'oculto')} | {p.get('comments_count', 0)} | {legenda} |"
        )
    return "\n".join(linhas) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("perfis", nargs="*", help="@ dos perfis (com ou sem @)")
    parser.add_argument("--posts", type=int, default=30, help="quantos posts recentes analisar (padrão 30)")
    parser.add_argument("--descobrir-id", action="store_true", help="mostra o IG_USER_ID da sua conta")
    args = parser.parse_args()

    carregar_env()
    if not os.environ.get("IG_ACCESS_TOKEN"):
        sys.exit("Falta IG_ACCESS_TOKEN. Veja docs/configurar-api-instagram.md.")

    if args.descobrir_id:
        descobrir_id()
        return
    if not os.environ.get("IG_USER_ID"):
        sys.exit("Falta IG_USER_ID. Rode com --descobrir-id para encontrá-lo.")
    if not args.perfis:
        parser.error("informe pelo menos um perfil")

    PASTA_SAIDA.mkdir(exist_ok=True)
    for usuario in (u.lstrip("@") for u in args.perfis):
        try:
            perfil = buscar_perfil(usuario, args.posts)
        except RuntimeError as erro:
            print(f"@{usuario}: erro — {erro}")
            continue
        base = PASTA_SAIDA / f"{date.today():%Y-%m-%d}-{usuario}"
        base.with_suffix(".json").write_text(json.dumps(perfil, ensure_ascii=False, indent=2), encoding="utf-8")
        base.with_suffix(".md").write_text(montar_relatorio(perfil), encoding="utf-8")
        print(f"@{usuario}: relatório salvo em {base.with_suffix('.md').relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
