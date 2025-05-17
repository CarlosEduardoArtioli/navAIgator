import gradio as gr
from gradio.themes import Base, Default, Soft, Monochrome, Glass, Origin, Citrus, Ocean  # Importar temas explicitamente

from src.webui.webui_manager import WebuiManager
from src.webui.components.agent_settings_tab import create_agent_settings_tab
from src.webui.components.browser_settings_tab import create_browser_settings_tab
from src.webui.components.browser_use_agent_tab import create_browser_use_agent_tab
from src.webui.components.deep_research_agent_tab import create_deep_research_agent_tab
from src.webui.components.load_save_config_tab import create_load_save_config_tab
from src.webui.components.rpa_challenge_tab import create_rpa_challenge_tab

# Cores da Accenture
ACCENTURE_PURPLE = "#A100FF"
ACCENTURE_BLACK = "#000000"
ACCENTURE_LIGHT_PURPLE = "#B459FF"
ACCENTURE_GREY = "#4A4A4A"

# Criar tema customizado para Accenture
accenture_theme = gr.Theme(
    primary_hue="purple",
    secondary_hue="gray",
    font=["Inter", "sans-serif"]
)

theme_map = {
    "Default": Default(),
    "Accenture": accenture_theme,
    "Soft": Soft(),
    "Monochrome": Monochrome(),
    "Glass": Glass(),
    "Origin": Origin(),
    "Citrus": Citrus(),
    "Ocean": Ocean(),
    "Base": Base()
}


def create_ui(theme_name="Accenture"):
    css = """
    .gradio-container {
        width: 70vw !important; 
        max-width: 70% !important; 
        margin-left: auto !important;
        margin-right: auto !important;
        padding-top: 10px !important;
    }
    .header-text {
        text-align: center;
        margin-bottom: 20px;
    }
    .tab-header-text {
        text-align: center;
    }
    .theme-section {
        margin-bottom: 10px;
        padding: 15px;
        border-radius: 10px;
    }
    /* Accenture logo and branding */
    .accenture-header {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 15px;
    }
    .accenture-logo {
        height: 40px;
        margin-right: 10px;
    }
    .accenture-title {
        font-weight: bold;
        font-size: 24px;
        color: #A100FF;
    }
    """

    # dark mode in default
    js_func = """
    function refresh() {
        const url = new URL(window.location);

        if (url.searchParams.get('__theme') !== 'dark') {
            url.searchParams.set('__theme', 'dark');
            window.location.href = url.href;
        }
    }
    """

    ui_manager = WebuiManager()

    with gr.Blocks(
            title="Test Navigator - Powered by Accenture", theme=theme_map[theme_name], css=css, js=js_func,
    ) as demo:
        with gr.Row():
            gr.Markdown(
                """
                <div class="accenture-header">
                <img src="https://upload.wikimedia.org/wikipedia/commons/c/cd/Accenture.svg" alt="Accenture Logo" class="accenture-logo">
                <span class="accenture-title">Test Navigator</span>
                </div>
                
                ### A ferramenta de testes automatizados inteligente
                """,
                elem_classes=["header-text"],
            )

        with gr.Tabs() as tabs:
            with gr.TabItem("⚙️ Configurações do Agente"):
                create_agent_settings_tab(ui_manager)

            with gr.TabItem("🌐 Configurações do Navegador"):
                create_browser_settings_tab(ui_manager)
                
            with gr.TabItem("🤖 Executar Agente"):
                create_browser_use_agent_tab(ui_manager)

            with gr.TabItem("🔍 Análise Avançada"):
                gr.Markdown(
                    """
                    ### Agentes especializados para testes
                    """,
                    elem_classes=["tab-header-text"],
                )
                with gr.Tabs():
                    with gr.TabItem("Pesquisa Profunda"):
                        create_deep_research_agent_tab(ui_manager)
                        
            with gr.TabItem("🏆 RPA Challenge"):
                create_rpa_challenge_tab(ui_manager)

            with gr.TabItem("📁 Configurações"):
                create_load_save_config_tab(ui_manager)

    return demo
