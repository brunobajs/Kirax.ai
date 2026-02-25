import streamlit as st
import requests
import json
import os
from PyPDF2 import PdfReader

# =========================================================
# CONFIGURAÇÃO DE ACESSO KIRAX (CHAVE VIA AMBIENTE/SEGREDO)
try:
    # Preferencialmente via st.secrets (Streamlit Cloud / local secrets.toml)
    CHAVE_MESTRA = st.secrets["OPENROUTER_API_KEY"]
except Exception:
    # Fallback para variável de ambiente
    CHAVE_MESTRA = os.environ.get("OPENROUTER_API_KEY", "")
# =========================================================


@st.cache_data(show_spinner=False)
def carregar_modelos(api_key: str):
    """
    Busca todos os modelos disponíveis no OpenRouter.
    Se falhar, volta para uma lista padrão.
    """
    modelos_padrao = [
        "google/gemini-2.0-flash-001",
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4o-mini",
        "deepseek/deepseek-chat",
    ]

    if not api_key:
        return modelos_padrao

    try:
        resp = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            modelos = [m.get("id", "") for m in data.get("data", []) if m.get("id")]
            return modelos or modelos_padrao
        return modelos_padrao
    except Exception:
        return modelos_padrao


def escolher_indice_modelo_padrao(modelos: list[str]) -> int:
    """
    Tenta escolher um modelo GPT-4 como padrão.
    Se não encontrar, usa o primeiro da lista.
    """
    preferidos = [
        "openai/gpt-4.1-mini",
        "openai/gpt-4o-mini",
        "openai/gpt-4.1",
        "openai/gpt-4o",
        "openai/gpt-4",
    ]
    for pref in preferidos:
        if pref in modelos:
            return modelos.index(pref)
    for i, mid in enumerate(modelos):
        if "gpt-4" in mid.lower():
            return i
    return 0

st.set_page_config(page_title="KIRAX.IA - Intelligence System", layout="wide")

# --- ESTILO VISUAL ---
st.markdown(
    """
    <style>
    /* Layout limpo: fundo escuro, texto claro, alto contraste */

    /* Área principal (direita) */
    [data-testid="stAppViewContainer"] > .main,
    [data-testid="stMain"] {
        background-color: #020617;
        color: #e5e7eb;
    }

    /* Sidebar: fundo escuro e texto branco para máxima leitura */
    [data-testid="stSidebar"] {
        background-color: #020617;
        border-right: 1px solid #111827;
        color: #ffffff;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {
        color: #ffffff !important;
    }

    h1, h2, h3 {
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-weight: 700;
        color: #f9fafb;
    }

    /* Botões discretos, com bom contraste */
    .stButton>button {
        border-radius: 999px;
        background-color: #38bdf8;
        color: #020617;
        border: none;
        font-weight: 600;
        font-size: 0.8rem;
        padding: 0.35rem 0.8rem;
    }

    .stButton>button:hover {
        background-color: #0ea5e9;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- DEFINIÇÃO DE PLANOS ---
PLANOS = {
    "Free": {
        "preco": "R$ 0 (teste 1–2 dias)",
        "publico": "Novo usuário testando a Kirax.IA antes de assinar.",
        "limites": "- Acesso por até 2 dias após cadastro\n- Limite reduzido de mensagens\n- Uso apenas para testes",
        "beneficios": "- Experiência completa de teste\n- Acesso aos principais especialistas Kirax\n- Ideal para validar se o produto serve para o negócio",
    },
    "Starter": {
        "preco": "R$ 49,90 / mês",
        "publico": "Profissionais, infoprodutores e pequenos negócios.",
        "limites": "- Volume de mensagens adequado para uso diário\n- Upload de múltiplos PDFs\n- Acesso a modelos mais avançados (conforme saldo no OpenRouter)",
        "beneficios": "- Todos os especialistas Kirax\n- Histórico estendido\n- Priorização moderada no suporte",
    },
    "Enterprise": {
        "preco": "R$ 149,90 / mês",
        "publico": "Empresas e times que precisam de volume maior, SLA e integrações.",
        "limites": "- Limites sob contrato\n- Acesso dedicado à infraestrutura",
        "beneficios": "- Onboarding dedicado\n- Treinamento de equipe\n- Integração com sistemas internos\n- Suporte com SLA",
    },
}


# --- ESTADO INICIAL DE PLANO ---
if "plano_escolhido" not in st.session_state:
    st.session_state.plano_escolhido = "Starter"

plano_escolhido = st.session_state.plano_escolhido
plano_info = PLANOS[plano_escolhido]


# --- CABEÇALHO COM LOGO, TÍTULO E BOTÃO DE PLANOS ---
header_logo_col, header_title_col, header_plans_col = st.columns([1.2, 3, 1.1])

with header_logo_col:
    logo_paths = [
        "logo_kirax.png",
        "logo.png",
        ".streamlit/logo_kirax.png",
        ".streamlit/logo.png",
        r"C:\Users\User\.cursor\projects\c-Users-User-OneDrive-rea-de-Trabalho-pasta-para-cursor\assets\c__Users_User_AppData_Roaming_Cursor_User_workspaceStorage_e2401c393076242d367c0b568e5aa692_images_logo_kirax-c0516406-a957-4a04-abd3-c826309b0868.png",
    ]
    for lp in logo_paths:
        if os.path.exists(lp):
            st.image(lp, width=220)
            break

with header_title_col:
    st.markdown("### KIRAX.IA")
    st.caption("Central de Inteligência Corporativa")

with header_plans_col:
    if "mostrar_planos" not in st.session_state:
        st.session_state.mostrar_planos = False

    if st.button("Planos", use_container_width=True):
        st.session_state.mostrar_planos = not st.session_state.mostrar_planos

st.divider()

if st.session_state.mostrar_planos:
    st.markdown("#### Planos de Assinatura")
    # seletor simples de plano
    novo_plano = st.selectbox(
        "Escolha seu plano:",
        list(PLANOS.keys()),
        index=list(PLANOS.keys()).index(plano_escolhido),
        key="plano_escolhido_select",
    )
    st.session_state.plano_escolhido = novo_plano
    plano_escolhido = novo_plano
    plano_info = PLANOS[plano_escolhido]

    for nome, info in PLANOS.items():
        with st.expander(nome, expanded=(nome == plano_escolhido)):
            st.markdown(f"**Preço:** {info['preco']}")
            st.markdown(f"**Para quem é:** {info['publico']}")
            st.markdown("**Limites:**")
            st.markdown(info["limites"])
            st.markdown("**Benefícios:**")
            st.markdown(info["beneficios"])

    st.divider()


# --- ÁREA PRINCIPAL: APENAS CHAT ---
st.subheader("Console de Conversa")

# Modelos disponíveis (para o seletor de modelo)
modelos_disponiveis = carregar_modelos(CHAVE_MESTRA)
if modelos_disponiveis:
    if "model_choice" not in st.session_state:
        default_index = escolher_indice_modelo_padrao(modelos_disponiveis)
    else:
        try:
            default_index = modelos_disponiveis.index(
                st.session_state["model_choice"]
            )
        except ValueError:
            default_index = escolher_indice_modelo_padrao(modelos_disponiveis)

    model_choice = st.selectbox(
        "Modelo de IA (padrão: GPT-4 quando disponível)",
        modelos_disponiveis,
        index=default_index,
        key="model_choice",
    )
else:
    model_choice = "indisponível"
    st.warning("Nenhum modelo foi encontrado no OpenRouter.")

# Linha com agente e gestão de dados logo abaixo da escolha de modelo
col_agent, col_pdf = st.columns(2)

agentes = {
    "Pesquisa Geral": "Você é o Kirax Research, um assistente geral de pesquisa e explicações claras. Ajude o usuário em qualquer assunto com linguagem simples e objetiva.",
    "Estrategista de Vendas": "Você é o Kirax Sales, focado em conversão e fechamento de negócios.",
    "Analista Jurídico": "Você é o Kirax Legal, especialista em análise técnica de contratos.",
    "Copywriter Senior": "Você é um mestre da persuasão. Crie textos que vendem imediatamente.",
    "Gestor de Tráfego": "Especialista em escala de anúncios e otimização de ROI.",
    "Analista de PDF": "Sua função é extrair informações e responder dúvidas sobre o arquivo enviado.",
    "Dev Helper": "Auxiliar em programação, depuração e arquitetura de sistemas.",
}

with col_agent:
    escolha = st.selectbox("Especialista ativo:", list(agentes.keys()), index=0)

with col_pdf:
    st.markdown("Gestão de Dados (PDF):")
    uploaded_file = st.file_uploader("Envie um PDF", type="pdf", label_visibility="collapsed")

contexto_pdf = ""
if uploaded_file:
    reader = PdfReader(uploaded_file)
    for page in reader.pages:
        contexto_pdf += page.extract_text()
    st.success("Dados do PDF integrados ao contexto.")

# Resumo simples das configurações ativas (linha única, usando o próprio tema do Streamlit)
st.write(
    f"**Plano:** {plano_escolhido}  |  **Modelo:** {st.session_state.get('model_choice', model_choice)}  |  **Especialista:** {escolha}"
)
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Insira o comando para Kirax..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        headers = {
            "Authorization": f"Bearer {CHAVE_MESTRA}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://kirax.ia",  # Identificador para o OpenRouter
            "X-Title": "Kirax IA",
        }

        system_msg = (
            f"Plano atual do usuário: {plano_escolhido}.\n"
            f"Descrição do plano: {plano_info['publico']}.\n\n"
            + agentes[escolha]
        )
        if contexto_pdf:
            system_msg += f"\n\n[DADOS DO ARQUIVO]:\n{contexto_pdf[:15000]}"

        payload = {
            "model": model_choice,
            "messages": [{"role": "system", "content": system_msg}]
            + st.session_state.messages,
        }

        try:
            res = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                data=json.dumps(payload),
            )
            if res.status_code == 200:
                resposta = res.json()["choices"][0]["message"]["content"]
                st.markdown(resposta)
                st.session_state.messages.append(
                    {"role": "assistant", "content": resposta}
                )
            else:
                st.error(
                    f"Erro {res.status_code}: Verifique o saldo ou a chave no OpenRouter."
                )
        except Exception:
            st.error("Falha Crítica: Sistema Temporariamente Indisponível.")
