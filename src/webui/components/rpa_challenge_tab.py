"""
Componente da interface para a aba RPA Challenge
"""

import asyncio
import logging
import os
from typing import Any, AsyncGenerator, Dict, Optional

import gradio as gr
from gradio.components import Component

from src.agent.rpa_challenge.rpa_challenge_agent import RPAChallengeRunner
from src.webui.webui_manager import WebuiManager
from src.utils import llm_provider

logger = logging.getLogger(__name__)

async def run_rpa_challenge(
    webui_manager: WebuiManager, components: Dict[gr.components.Component, Any]
) -> AsyncGenerator[Dict[gr.components.Component, Any], None]:
    """
    Function to execute the RPA Challenge
    """
    # Obtém os componentes da interface
    run_button_comp = webui_manager.get_component_by_id("rpa_challenge.run_button")
    stop_button_comp = webui_manager.get_component_by_id("rpa_challenge.stop_button")
    status_comp = webui_manager.get_component_by_id("rpa_challenge.status")
    headless_comp = webui_manager.get_component_by_id("rpa_challenge.headless")
    download_gif_comp = webui_manager.get_component_by_id("rpa_challenge.download_gif")
    process_gif_comp = webui_manager.get_component_by_id("rpa_challenge.process_gif")
    log_output_comp = webui_manager.get_component_by_id("rpa_challenge.log_output")

    # Atualiza a interface para indicar que o processo está em execução
    yield {
                    run_button_comp: gr.update(interactive=False, value="⏳ Running..."),
        stop_button_comp: gr.update(interactive=True),
        status_comp: gr.update(value="Iniciando o RPA Challenge..."),
        log_output_comp: gr.update(value="Iniciando o RPA Challenge...\n"),
    }

    try:
        # Get agent configurations
        headless = components.get(headless_comp, True)
        
        # Get LLM configurations
        provider_comp = webui_manager.get_component_by_id("agent_settings.llm_provider")
        model_comp = webui_manager.get_component_by_id("agent_settings.llm_model_name")
        temperature_comp = webui_manager.get_component_by_id("agent_settings.llm_temperature")
        base_url_comp = webui_manager.get_component_by_id("agent_settings.llm_base_url")
        api_key_comp = webui_manager.get_component_by_id("agent_settings.llm_api_key")
        
        provider = components.get(provider_comp, None)
        model_name = components.get(model_comp, None)
        temperature = components.get(temperature_comp, 0.6)
        base_url = components.get(base_url_comp, None)
        api_key = components.get(api_key_comp, None)
        
        # Check if LLM settings are present
        if not provider or not model_name:
            yield {
                status_comp: gr.update(value="Error: LLM not configured. Configure in Agent Settings."),
                run_button_comp: gr.update(interactive=True, value="▶️ Run RPA Challenge"),
                stop_button_comp: gr.update(interactive=False),
                log_output_comp: gr.update(value="Error: LLM not configured. Configure in Agent Settings."),
            }
            return
            
        # Initialize LLM
        yield {
            status_comp: gr.update(value="Initializing LLM..."),
            log_output_comp: gr.update(value="Initializing LLM...\n"),
        }
        
        # Tenta inicializar o LLM
        llm = llm_provider.get_llm_model(
            provider=provider,
            model_name=model_name,
            temperature=temperature,
            base_url=base_url,
            api_key=api_key,
        )
        
        # Cria o runner do RPA Challenge
        runner = RPAChallengeRunner(webui_manager)
        webui_manager.rpa_challenge_runner = runner
        
        # Inicializa o navegador
        yield {
            status_comp: gr.update(value="Inicializando navegador..."),
            log_output_comp: gr.update(value=components.get(log_output_comp, "") + "Inicializando navegador...\n"),
        }
        
        success = await runner.initialize_browser(headless=headless)
        if not success:
            raise Exception("Falha ao inicializar o navegador")
        
        # Define o callback de conclusão
        async def on_done_callback(results):
            # Atualiza a interface com os resultados
            result_updates = {
                run_button_comp: gr.update(interactive=True, value="▶️ Executar RPA Challenge"),
                stop_button_comp: gr.update(interactive=False),
            }
            
            if results["success"]:
                result_updates[status_comp] = gr.update(value="RPA Challenge concluído com sucesso!")
            else:
                result_updates[status_comp] = gr.update(value=f"Erro no RPA Challenge: {results.get('error', 'Erro desconhecido')}")
            
            # Atualiza os GIFs
            if results.get("download_gif") and os.path.exists(results["download_gif"]):
                result_updates[download_gif_comp] = gr.update(value=results["download_gif"], visible=True)
            
            if results.get("process_gif") and os.path.exists(results["process_gif"]):
                result_updates[process_gif_comp] = gr.update(value=results["process_gif"], visible=True)
            
            # Atualiza o log
            if results.get("summary"):
                current_log = components.get(log_output_comp, "")
                result_updates[log_output_comp] = gr.update(value=current_log + "\n\n" + results["summary"])
            
            return result_updates
        
        # Executa a automação
        yield {
            status_comp: gr.update(value="Executando RPA Challenge..."),
            log_output_comp: gr.update(value=components.get(log_output_comp, "") + "Executando RPA Challenge...\n"),
        }
        
        # Executa de forma assíncrona para não bloquear a interface
        task = asyncio.create_task(runner.run_automation(llm))
        webui_manager.rpa_challenge_task = task
        
        # Aguarda a conclusão
        results = await task
        webui_manager.rpa_challenge_task = None
        
        # Atualiza a interface com os resultados
        updates = await on_done_callback(results)
        yield updates
            
    except asyncio.CancelledError:
        logger.info("RPA Challenge cancelado pelo usuário")
        yield {
            status_comp: gr.update(value="RPA Challenge cancelado pelo usuário"),
            run_button_comp: gr.update(interactive=True, value="▶️ Executar RPA Challenge"),
            stop_button_comp: gr.update(interactive=False),
            log_output_comp: gr.update(value=components.get(log_output_comp, "") + "\nRPA Challenge cancelado pelo usuário"),
        }
    except Exception as e:
        logger.error(f"Erro ao executar RPA Challenge: {e}", exc_info=True)
        yield {
            status_comp: gr.update(value=f"Erro: {str(e)}"),
            run_button_comp: gr.update(interactive=True, value="▶️ Executar RPA Challenge"),
            stop_button_comp: gr.update(interactive=False),
            log_output_comp: gr.update(value=components.get(log_output_comp, "") + f"\nErro ao executar RPA Challenge: {str(e)}"),
        }

async def handle_stop(webui_manager: WebuiManager):
    """
    Manipulador para o botão de parar
    """
    logger.info("Parando RPA Challenge...")
    
    if hasattr(webui_manager, "rpa_challenge_task") and webui_manager.rpa_challenge_task:
        # Cancela a tarefa
        webui_manager.rpa_challenge_task.cancel()
        webui_manager.rpa_challenge_task = None
    
    # Fecha os recursos do runner
    if hasattr(webui_manager, "rpa_challenge_runner") and webui_manager.rpa_challenge_runner:
        await webui_manager.rpa_challenge_runner.close_resources()
    
    return {
        webui_manager.get_component_by_id("rpa_challenge.status"): gr.update(value="RPA Challenge interrompido"),
        webui_manager.get_component_by_id("rpa_challenge.run_button"): gr.update(interactive=True, value="▶️ Executar RPA Challenge"),
        webui_manager.get_component_by_id("rpa_challenge.stop_button"): gr.update(interactive=False),
    }

async def handle_clear(webui_manager: WebuiManager):
    """
    Manipulador para o botão de limpar
    """
    logger.info("Limpando interface do RPA Challenge...")
    
    # Fecha os recursos do runner
    if hasattr(webui_manager, "rpa_challenge_runner") and webui_manager.rpa_challenge_runner:
        await webui_manager.rpa_challenge_runner.close_resources()
        webui_manager.rpa_challenge_runner = None
    
    return {
        webui_manager.get_component_by_id("rpa_challenge.status"): gr.update(value=""),
        webui_manager.get_component_by_id("rpa_challenge.log_output"): gr.update(value=""),
        webui_manager.get_component_by_id("rpa_challenge.download_gif"): gr.update(value=None, visible=False),
        webui_manager.get_component_by_id("rpa_challenge.process_gif"): gr.update(value=None, visible=False),
    }

def create_rpa_challenge_tab(webui_manager: WebuiManager):
    """
    Cria a aba do RPA Challenge na interface
    """
    webui_manager.init_rpa_challenge()
    
    tab_components = {}
    with gr.Column():
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown(
                    """
                    ### RPA Challenge
                    
                    This tab allows you to run an automation for the [RPA Challenge](https://rpachallenge.com/), 
                    a form filling automation challenge.
                    
                    The challenge consists of:
                    1. Download an Excel file with data
                    2. Fill a form with the Excel data
                    
                    The automation uses two agents:
                    - Excel download agent
                    - Form filling agent
                    """,
                    elem_classes=["tab-header-text"],
                )
                status = gr.Textbox(
                    label="Status", 
                    placeholder="RPA Challenge execution status",
                    interactive=False,
                    lines=1
                )
            with gr.Column(scale=1):
                headless = gr.Checkbox(
                    label="Run in headless mode", 
                    value=True,
                    info="If checked, the browser will run in the background"
                )
                with gr.Row():
                    run_button = gr.Button(
                        "▶️ Run RPA Challenge", 
                        variant="primary", 
                        scale=1
                    )
                    stop_button = gr.Button(
                        "⏹️ Stop", 
                        variant="stop", 
                        scale=1,
                        interactive=False
                    )
                    clear_button = gr.Button(
                        "🗑️ Clear", 
                        variant="secondary", 
                        scale=1
                    )
        
        with gr.Tabs():
            with gr.TabItem("📊 Results"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### Download Agent")
                        download_gif = gr.Image(
                            label="Download Recording",
                            visible=False,
                            type="filepath",
                            format="gif"
                        )
                    with gr.Column(scale=1):
                        gr.Markdown("### Processing Agent")
                        process_gif = gr.Image(
                            label="Processing Recording",
                            visible=False,
                            type="filepath",
                            format="gif"
                        )
            with gr.TabItem("📝 Logs"):
                log_output = gr.Textbox(
                    label="Logs", 
                    placeholder="RPA Challenge execution logs",
                    interactive=False,
                    lines=20
                )
    
    # Registra os componentes
    tab_components.update(
        dict(
            status=status,
            headless=headless,
            run_button=run_button,
            stop_button=stop_button,
            clear_button=clear_button,
            download_gif=download_gif,
            process_gif=process_gif,
            log_output=log_output
        )
    )
    webui_manager.add_components("rpa_challenge", tab_components)
    
    # Prepara os componentes para os callbacks
    all_managed_components = set(webui_manager.get_components())
    tab_outputs = list(tab_components.values())
    
    # Wrappers para os callbacks
    async def run_wrapper(components_dict):
        async for update in run_rpa_challenge(webui_manager, components_dict):
            yield update
    
    async def stop_wrapper():
        updates = await handle_stop(webui_manager)
        yield updates
    
    async def clear_wrapper():
        updates = await handle_clear(webui_manager)
        yield updates
    
    # Registra os callbacks
    run_button.click(
        fn=run_wrapper,
        inputs=all_managed_components,
        outputs=tab_outputs
    )
    
    stop_button.click(
        fn=stop_wrapper,
        inputs=None,
        outputs=tab_outputs
    )
    
    clear_button.click(
        fn=clear_wrapper,
        inputs=None,
        outputs=tab_outputs
    ) 