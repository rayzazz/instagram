# Configurar a API do Instagram (Business Discovery)

Configuração feita **uma vez só** (30–60 min). Depois disso é só passar os @ que
o Claude gera os relatórios dos perfis em `analises/`.

> Os nomes dos menus da Meta mudam com frequência. Se algo estiver diferente
> do que está escrito aqui, tire um print e mande na conversa.

## O que funciona e o que não funciona

- ✅ Perfis **profissionais** (Criador de conteúdo ou Empresa): seguidores, bio,
  nº de posts, legendas, curtidas, comentários, datas e formato dos posts.
- ❌ Contas pessoais, stories, visualizações de Reels, salvamentos e compartilhamentos.
- Curtidas que o dono ocultou aparecem como "oculto".

---

## Passo 1 — Transformar sua conta em profissional

No app do Instagram: **Perfil → ☰ → Configurações e privacidade → Tipo de conta
e ferramentas → Mudar para conta profissional → Criador de conteúdo**.
Categoria sugerida: *Educação* ou *Criador(a) digital*.

## Passo 2 — Criar uma Página do Facebook e vincular ao Instagram

1. No Facebook, crie uma Página (pode ser simples, com o mesmo nome do perfil).
   Ela não precisa ter posts nem ser divulgada.
2. Na Página: **Configurações → Contas vinculadas → Instagram → Conectar**
   (ou pelo Meta Business Suite: **Configurações → Contas do Instagram**).

## Passo 3 — Criar um app no Meta for Developers

1. Acesse <https://developers.facebook.com> e entre com seu Facebook.
   Se pedir, conclua o cadastro de desenvolvedor (é gratuito).
2. **Meus apps → Criar app**.
3. No caso de uso, escolha **Outro**; no tipo de app, **Empresa** (Business).
   Nome sugerido: `analise-perfis`.
4. No painel do app, adicione o produto **Instagram** e escolha a opção de
   configuração **com login do Facebook** (*API setup with Facebook login*).
   ⚠️ A opção "com login do Instagram" **não** tem Business Discovery.

O app pode ficar em **modo de desenvolvimento**: como você é a administradora,
não precisa passar pela revisão da Meta.

## Passo 4 — Gerar o token de acesso

1. Abra o **Graph API Explorer**: <https://developers.facebook.com/tools/explorer>
2. Em *Meta App*, selecione o app que você criou.
3. Em *User or Page*, escolha **Get User Access Token** e marque as permissões:
   - `instagram_basic`
   - `pages_show_list`
   - `pages_read_engagement`
   - `business_management`
4. Clique em **Generate Access Token** e, na janela do Facebook, autorize
   **a sua Página e a sua conta do Instagram**.

## Passo 5 — Transformar em token de longa duração (60 dias)

O token do passo 4 expira em cerca de 1 hora.

1. Clique no ícone ⓘ ao lado do token → **Open in Access Token Tool**
   (ou acesse <https://developers.facebook.com/tools/debug/accesstoken>).
2. Clique em **Extend Access Token** e copie o novo token.
3. Anote a data: daqui a ~60 dias será preciso repetir os passos 4 e 5.

## Passo 6 — Descobrir o seu IG_USER_ID

No Graph API Explorer, com o token selecionado, rode a consulta:

```
me/accounts?fields=name,instagram_business_account{id,username}
```

O número em `instagram_business_account → id` é o seu **IG_USER_ID**
(é diferente do número que aparece no app do Instagram).

## Passo 7 — Guardar as credenciais (sem colar no chat!)

**Nunca cole o token na conversa nem faça commit dele no repositório.**

**Na sessão do Claude na nuvem:** menu do ambiente na barra de título da
sessão → **Edit** → adicione as variáveis de ambiente:

```
IG_ACCESS_TOKEN=<token do passo 5>
IG_USER_ID=<id do passo 6>
```

Uma **sessão nova** passa a enxergar as variáveis. Abra uma sessão nova neste
repositório e peça: *"analisa os perfis @fulana e @ciclana"*.

**No seu computador (opcional):** copie `.env.example` para `.env`, preencha
e rode:

```bash
python3 scripts/analisar_perfis.py --descobrir-id        # confere a conexão
python3 scripts/analisar_perfis.py fulana ciclana --posts 30
```

O `.env` já está no `.gitignore`, então não vai para o GitHub.

---

## Problemas comuns

| Erro | O que fazer |
|---|---|
| `Error validating access token` / `Session has expired` | Token venceu: refaça os passos 4 e 5. |
| `Invalid user id` / `Cannot find User` | O perfil pesquisado é pessoal ou o @ está errado. |
| `(#10) Application does not have permission` | Faltou marcar alguma permissão do passo 4. |
| `--descobrir-id` não encontra nada | O Instagram não está vinculado à Página (passo 2) ou não foi autorizado no passo 4. |
