"""
Aba de monitoramento e configuração do Laminar
"""
import gradio as gr
import os
from src.integrations.laminar_config import laminar_config, is_laminar_enabled, log_metric


def create_laminar_monitoring_tab(webui_manager):
    """Cria a aba de monitoramento do Laminar"""
    
    def check_laminar_status():
        """Verifica o status atual do Laminar"""
        if is_laminar_enabled():
            return "✅ Laminar está ativo e funcionando", "success"
        elif laminar_config.project_api_key:
            return "⚠️ Laminar configurado mas não inicializado", "warning"
        else:
            return "❌ Laminar não configurado", "error"
    
    def get_current_config():
        """Retorna a configuração atual do Laminar"""
        return {
            "API Key": "***" + (laminar_config.project_api_key[-8:] if laminar_config.project_api_key else "Não configurada"),
            "Base URL": laminar_config.base_url,
            "Habilitado": "Sim" if laminar_config.enabled else "Não",
            "Inicializado": "Sim" if laminar_config.initialized else "Não"
        }
    
    def test_laminar_connection():
        """Testa a conexão com o Laminar"""
        try:
            if not is_laminar_enabled():
                return "❌ Laminar não está habilitado ou configurado"
            
            # Enviar uma métrica de teste
            log_metric("connection_test", "success", {"timestamp": "now"})
            return "✅ Conexão com Laminar testada com sucesso!"
        except Exception as e:
            return f"❌ Erro ao testar conexão: {str(e)}"
    
    def update_laminar_config(api_key, base_url, enabled):
        """Atualiza a configuração do Laminar"""
        try:
            # Atualizar variáveis de ambiente
            if api_key and api_key.strip():
                os.environ['LMNR_PROJECT_API_KEY'] = api_key.strip()
            if base_url and base_url.strip():
                os.environ['LMNR_BASE_URL'] = base_url.strip()
            os.environ['LMNR_ENABLED'] = 'true' if enabled else 'false'
            
            # Reinicializar configuração
            laminar_config.__init__()
            success = laminar_config.initialize()
            
            if success:
                return "✅ Configuração atualizada e Laminar reinicializado com sucesso!"
            else:
                return "⚠️ Configuração atualizada, mas falha na inicialização do Laminar"
        except Exception as e:
            return f"❌ Erro ao atualizar configuração: {str(e)}"
    
    with gr.Column():
        gr.Markdown(
            """
            ### 📊 Monitoramento Laminar
            Configure e monitore a integração com o Laminar para observabilidade de IA
            """,
            elem_classes=["tab-header-text"],
        )
        
        # Status atual
        with gr.Row():
            with gr.Column(scale=2):
                status_text = gr.Textbox(
                    label="Status do Laminar",
                    value=check_laminar_status()[0],
                    interactive=False,
                    elem_id="laminar_monitoring.status"
                )
            with gr.Column(scale=1):
                refresh_btn = gr.Button("🔄 Atualizar Status", size="sm")
        
        # Configuração atual
        with gr.Row():
            config_display = gr.JSON(
                label="Configuração Atual",
                value=get_current_config(),
                elem_id="laminar_monitoring.config_display"
            )
        
        # Configurações
        gr.Markdown("#### ⚙️ Configurações")
        with gr.Row():
            with gr.Column():
                api_key_input = gr.Textbox(
                    label="Chave da API do Projeto",
                    placeholder="Insira sua chave da API do Laminar",
                    type="password",
                    elem_id="laminar_monitoring.api_key"
                )
                base_url_input = gr.Textbox(
                    label="URL Base",
                    value="https://api.lmnr.ai",
                    placeholder="URL do servidor Laminar",
                    elem_id="laminar_monitoring.base_url"
                )
                enabled_checkbox = gr.Checkbox(
                    label="Habilitar Laminar",
                    value=True,
                    elem_id="laminar_monitoring.enabled"
                )
        
        # Botões de ação
        with gr.Row():
            test_btn = gr.Button("🧪 Testar Conexão", variant="secondary")
            save_btn = gr.Button("💾 Salvar Configuração", variant="primary")
        
        # Resultado das ações
        result_text = gr.Textbox(
            label="Resultado",
            interactive=False,
            elem_id="laminar_monitoring.result"
        )
        
        # Informações e links úteis
        gr.Markdown(
            """
            #### 📚 Informações Úteis
            
            **Como obter uma chave da API:**
            1. Acesse [lmnr.ai](https://www.lmnr.ai/)
            2. Crie uma conta e um projeto
            3. Vá em Settings → API Keys
            4. Gere uma nova chave da API
            
            **Self-hosting:**
            - Para usar uma instância própria do Laminar, altere a URL Base
            - Documentação: [docs.lmnr.ai](https://docs.lmnr.ai/)
            
            **Recursos monitorados:**
            - ✅ Execução de tarefas do agente
            - ✅ Ações do navegador
            - ✅ Tempo de execução
            - ✅ Taxa de sucesso/erro
            - ✅ Métricas de performance
            """
        )
        
        # Event handlers
        def refresh_status():
            status, _ = check_laminar_status()
            config = get_current_config()
            return status, config
        
        refresh_btn.click(
            fn=refresh_status,
            outputs=[status_text, config_display]
        )
        
        test_btn.click(
            fn=test_laminar_connection,
            outputs=[result_text]
        )
        
        save_btn.click(
            fn=update_laminar_config,
            inputs=[api_key_input, base_url_input, enabled_checkbox],
            outputs=[result_text]
        ).then(
            fn=refresh_status,
            outputs=[status_text, config_display]
        )
    
    # Registrar componentes no webui_manager
    components_dict = {
        "status": status_text,
        "config_display": config_display,
        "api_key": api_key_input,
        "base_url": base_url_input,
        "enabled": enabled_checkbox,
        "result": result_text
    }
    webui_manager.add_components("laminar_monitoring", components_dict) 