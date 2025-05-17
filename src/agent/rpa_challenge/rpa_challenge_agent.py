"""
Módulo de automação RPA para o RPA Challenge usando múltiplos agentes e Excel.
RPA automation module for RPA Challenge using multiple agents and Excel.

Este módulo implementa uma solução automatizada para o RPA Challenge, utilizando dois agentes:
1. Um agente para download do arquivo Excel
2. Um agente para preenchimento do formulário com os dados do Excel
"""

import asyncio
import os
import glob
import warnings
import logging
import uuid
import json
import requests
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

import pandas as pd
from functools import lru_cache
from browser_use.agent.views import AgentHistoryList, AgentOutput
from browser_use.browser.browser import BrowserConfig
from browser_use.browser.context import BrowserContextConfig

from src.agent.browser_use.browser_use_agent import BrowserUseAgent
from src.browser.custom_browser import CustomBrowser
from src.controller.custom_controller import CustomController

# Suprime avisos de recursos não fechados
warnings.filterwarnings("ignore", category=ResourceWarning)

logger = logging.getLogger(__name__)

# Define e cria os diretórios necessários
BASE_DIR = Path('./tmp/rpa_challenge')  # Coloca no diretório tmp para seguir o padrão do NavAIgator
DOWNLOADS_DIR = BASE_DIR / 'downloads'
LOGS_DIR = BASE_DIR / 'logs'
RECORDINGS_DIR = BASE_DIR / 'recordings'
SCRIPT_DIR = BASE_DIR / 'playwright_scripts'

# Cria os diretórios se não existirem
for directory in [BASE_DIR, DOWNLOADS_DIR, LOGS_DIR, RECORDINGS_DIR, SCRIPT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Cache para armazenar os dados do Excel em memória
@lru_cache(maxsize=1)
def read_excel_data(file_path):
    """
    Versão em cache da função read_excel_data para melhor performance.
    
    Args:
        file_path (str): Caminho do arquivo Excel
        
    Returns:
        list: Lista de dicionários contendo os dados do Excel
    """
    try:
        df = pd.read_excel(file_path)
        return df.to_dict('records')
    except Exception as e:
        logger.error(f"Erro ao ler o arquivo Excel: {e}")
        return None

def find_latest_challenge_file():
    """
    Encontra o arquivo Excel mais recente que contenha 'challenge' no nome.
    
    Returns:
        str: Caminho do arquivo mais recente ou None se nenhum arquivo for encontrado
    """
    # Verifica se o arquivo baixado diretamente existe
    direct_file = DOWNLOADS_DIR / "challenge_direct.xlsx"
    if direct_file.exists() and direct_file.stat().st_size > 0:
        logger.info(f"Encontrado arquivo baixado diretamente: {direct_file}")
        try:
            # Verifica se é um arquivo Excel válido
            pd.read_excel(direct_file)
            return str(direct_file)
        except Exception as e:
            logger.error(f"Erro ao ler arquivo direto: {e}")
            # Se falhar, exclui o arquivo corrompido
            try:
                os.remove(direct_file)
                logger.info(f"Arquivo corrompido removido: {direct_file}")
            except:
                pass
    
    # Caso contrário, procura por qualquer arquivo com 'challenge' no nome
    pattern = str(DOWNLOADS_DIR / '*challenge*.xlsx')
    files = glob.glob(pattern)
    
    # Filtra para manter apenas arquivos válidos
    valid_files = []
    for file in files:
        try:
            if os.path.getsize(file) > 0:
                # Tenta abrir para verificar se é um Excel válido
                pd.read_excel(file)
                valid_files.append(file)
            else:
                logger.warning(f"Arquivo com tamanho zero: {file}")
        except Exception as e:
            logger.error(f"Arquivo inválido {file}: {e}")
            # Remove arquivo corrompido
            try:
                os.remove(file)
                logger.info(f"Arquivo corrompido removido: {file}")
            except:
                pass
    
    if not valid_files:
        return None
    
    latest_file = max(valid_files, key=os.path.getctime)
    logger.info(f"Encontrado arquivo mais recente válido: {latest_file}")
    return latest_file

async def process_excel_data():
    """
    Processa o arquivo Excel baixado e retorna os dados.
    
    Returns:
        list: Dados do Excel processados
        
    Raises:
        Exception: Se não for possível encontrar ou ler o arquivo Excel
    """
    excel_file = find_latest_challenge_file()
    if not excel_file:
        raise Exception("Não foi possível encontrar o arquivo Excel baixado")
    
    logger.info(f"Arquivo encontrado: {excel_file}")
    
    # Usa a versão em cache da função
    excel_data = read_excel_data(excel_file)
    if not excel_data:
        raise Exception("Não foi possível ler os dados do arquivo Excel")
    
    logger.info(f"Dados lidos do Excel: {len(excel_data)} registros")
    return excel_data

def get_script_path(base_name):
    """
    Gera um nome de arquivo único para o script com timestamp.
    
    Args:
        base_name (str): Nome base do script
        
    Returns:
        Path: Caminho completo do arquivo
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return SCRIPT_DIR / f"{base_name}_{timestamp}.py"

def log_agent_history(agent_name, history, result_lines):
    """
    Registra o histórico de execução do agente.
    
    Args:
        agent_name (str): Nome do agente
        history: Histórico do agente
        result_lines (list): Lista para armazenar as linhas de resultado
    """
    if not history:
        result_lines.append(f"\n===== {agent_name} =====\nNenhum histórico disponível")
        return
        
    result_lines.append(f"\n===== {agent_name} =====")
    
    # Métodos que podem existir na classe AgentHistoryList
    possible_methods = [
        ("URLs visitados", "urls", []),
        ("Ações executadas", "action_names", []),
        ("Conteúdo extraído", "extracted_content", []),
        ("Erros", "errors", []),
        ("Ações do modelo", "model_actions", []),
        ("Resultado final", "final_result", None),
        ("Completou com sucesso", "is_done", False),
        ("Completou com sucesso (validação)", "is_successful", False),
        ("Pensamentos do modelo", "model_thoughts", []),
        ("Resultados das ações", "action_results", []),
        ("Número de passos", "number_of_steps", 0),
        ("Tokens usados", "total_input_tokens", 0),
        ("Tokens por passo", "input_token_usage", {}),
        ("Duração total (s)", "total_duration_seconds", 0)
    ]
    
    for label, method_name, default in possible_methods:
        try:
            if hasattr(history, method_name):
                method = getattr(history, method_name)
                if callable(method):
                    value = method()
                else:
                    value = method
                result_lines.append(f"{label}: {value}")
        except Exception as e:
            result_lines.append(f"{label}: Erro ao obter ({e})")
    
    # Cálculo do custo estimado para GPT-4o (input)
    try:
        COST_PER_INPUT_TOKEN = 0.000005
        input_tokens = history.total_input_tokens()
        cost = input_tokens * COST_PER_INPUT_TOKEN
        result_lines.append(f"Custo estimado (input): ${cost:.6f}")
    except Exception as e:
        result_lines.append(f"Custo estimado (input): Erro ao calcular ({e})")

class RPAChallengeRunner:
    """
    Classe responsável por executar o desafio RPA Challenge
    """
    
    def __init__(self, webui_manager):
        """
        Inicializa o executor do RPA Challenge
        
        Args:
            webui_manager: Instância do gerenciador de UI
        """
        self.webui_manager = webui_manager
        self.download_agent = None
        self.process_agent = None
        self.browser = None
        self.context = None
        self.run_id = str(uuid.uuid4())
        
        # Paths para arquivos de saída
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.download_script_path = get_script_path("playwright_download_script")
        self.process_script_path = get_script_path("playwright_process_script")
        self.download_gif_path = str(RECORDINGS_DIR / f"download_agent_{timestamp}.gif")
        self.process_gif_path = str(RECORDINGS_DIR / f"process_agent_{timestamp}.gif")
        self.result_file = LOGS_DIR / f"resultados_{timestamp}.txt"
        
    async def initialize_browser(self, headless=False):
        """
        Inicializa o navegador com as configurações adequadas
        
        Args:
            headless (bool): Se o navegador deve ser executado em modo headless
            
        Returns:
            bool: True se a inicialização foi bem-sucedida, False caso contrário
        """
        try:
            # Configuração do browser com parâmetros otimizados
            self.browser = CustomBrowser(
                config=BrowserConfig(
                    headless=headless,
                    disable_security=True,
                    extra_browser_args=[
                        f"--window-size=1280,720",
                        "--disable-web-security",
                        "--disable-features=IsolateOrigins,site-per-process",
                    ]
                )
            )
            
            # Configuração do contexto
            self.context = await self.browser.new_context(
                config=BrowserContextConfig(
                    save_downloads_path=str(DOWNLOADS_DIR),
                    window_width=1280,
                    window_height=720,
                    save_recording_path=str(RECORDINGS_DIR),
                )
            )
            
            # Adicionar configurações adicionais para download usando a página padrão no run_download_agent
            
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar o navegador: {e}")
            return False
    
    async def close_resources(self):
        """
        Fecha recursos como navegador e contexto
        """
        try:
            if self.context:
                await self.context.close()
                self.context = None
                
            if self.browser:
                await self.browser.close()
                self.browser = None
        except Exception as e:
            logger.error(f"Erro ao fechar recursos: {e}")
    
    async def run_download_agent(self, llm):
        """
        Executa o agente de download do Excel
        
        Args:
            llm: Modelo de linguagem a ser usado
            
        Returns:
            AgentHistoryList: Histórico da execução do agente
        """
        if not self.context:
            raise ValueError("Browser context não inicializado")
            
        logger.info("Iniciando agente de download...")
        
        # Primeiro tenta fazer o download direto usando urllib.request
        try:
            logger.info("Tentando download direto via HTTP request...")
            
            # URL do arquivo Excel no site RPA Challenge
            excel_url = "https://rpachallenge.com/assets/downloadFiles/challenge.xlsx"
            
            # Caminho onde o arquivo será salvo
            direct_download_path = DOWNLOADS_DIR / "challenge_direct.xlsx"
            
            # Fazer o download usando urllib.request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            req = urllib.request.Request(excel_url, headers=headers)
            with urllib.request.urlopen(req) as response:
                excel_content = response.read()
                
            # Salvar o conteúdo no arquivo
            with open(direct_download_path, 'wb') as f:
                f.write(excel_content)
                
            logger.info(f"Download direto concluído com sucesso: {direct_download_path}")
            
            # Verificar se o arquivo foi baixado corretamente
            if os.path.exists(direct_download_path) and os.path.getsize(direct_download_path) > 0:
                # Verificar se o arquivo é válido como Excel
                try:
                    # Tentar abrir o arquivo para verificar se é um Excel válido
                    test_df = pd.read_excel(direct_download_path)
                    if len(test_df) > 0:
                        logger.info(f"Arquivo Excel válido com {len(test_df)} linhas")
                        
                        # Configurar o controlador e o agente
                        controller = CustomController()
                        
                        # Configurar o agente apenas para abrir o site (não precisamos baixar o arquivo)
                        self.download_agent = BrowserUseAgent(
                            task='''1. Acesse o site "https://rpachallenge.com/".
                                  2. Apenas verifique que a página carregou corretamente.
                                  3. NÃO clique no botão "Start" ainda, pois isso será feito pelo próximo agente.
                                  4. Retorne "Página carregada com sucesso".''',
                            llm=llm,
                            browser=self.browser,
                            browser_context=self.context,
                            controller=controller,
                            max_actions_per_step=10,
                            use_vision=True,
                            max_failures=3,
                            generate_gif=self.download_gif_path,
                            save_playwright_script_path=str(self.download_script_path),
                            source="webui",
                        )
                        
                        # Executar o agente apenas para abrir o site
                        download_history = await asyncio.wait_for(
                            self.download_agent.run(max_steps=5),
                            timeout=60
                        )
                        
                        return download_history
                    else:
                        logger.warning("Arquivo Excel parece estar vazio, tentando com agente...")
                except Exception as excel_err:
                    logger.error(f"Erro ao validar arquivo Excel: {excel_err}")
        
        except Exception as e:
            logger.error(f"Erro no download direto: {e}")
            logger.info("Continuando com download via agente...")
        
        # Configura o controlador
        controller = CustomController()
        
        # Configura o agente
        self.download_agent = BrowserUseAgent(
            task='''1. Acesse o site "https://rpachallenge.com/".
                  2. Clique no botão "Download Excel" para baixar o arquivo.
                  3. Aguarde alguns segundos para garantir que o download seja concluído.
                  4. NÃO clique no botão "Start" ainda, pois isso será feito pelo próximo agente.
                  5. Após verificar que o download foi concluído, informe "Download concluído com sucesso".''',
            llm=llm,
            browser=self.browser,
            browser_context=self.context,
            controller=controller,
            max_actions_per_step=50,
            use_vision=True,
            max_failures=5,
            generate_gif=self.download_gif_path,
            save_playwright_script_path=str(self.download_script_path),
            source="webui",
        )
        
        # Executa o agente com retry e timeout
        try:
            download_history = await asyncio.wait_for(
                self.download_agent.run(max_steps=25),
                timeout=300
            )
        except asyncio.TimeoutError:
            logger.warning("Timeout no agente de download, tentando novamente...")
            download_history = await asyncio.wait_for(
                self.download_agent.run(max_steps=25),
                timeout=300
            )
            
        return download_history
    
    async def run_process_agent(self, llm, excel_data):
        """
        Executa o agente de processamento do formulário
        
        Args:
            llm: Modelo de linguagem a ser usado
            excel_data: Dados do Excel para preenchimento do formulário
            
        Returns:
            AgentHistoryList: Histórico da execução do agente
        """
        if not self.context:
            raise ValueError("Browser context não inicializado")
            
        logger.info("Iniciando agente de processamento...")
        
        # Configura o controlador
        controller = CustomController()
        
        # Configura o agente
        self.process_agent = BrowserUseAgent(
            task=f'''
                Esta tarefa consiste em preencher formulários do RPA Challenge com dados de uma planilha Excel.
                
                Passos:
                1. IMPORTANTE: Primeiro, clique no botão "START" no site para iniciar o desafio.
                2. Preencha o formulário RPA Challenge com os seguintes dados da planilha:
                {excel_data}
                
                Para cada registro da planilha, preencha os seguintes campos no formulário:
                - "First Name" → Digite o valor da coluna "First Name"
                - "Last Name" → Digite o valor da coluna "Last Name"
                - "Company Name" → Digite o valor da coluna "Company Name"
                - "Role in Company" → Digite o valor da coluna "Role in Company"
                - "Address" → Digite o valor da coluna "Address"
                - "Email" → Digite o valor da coluna "Email"
                - "Phone Number" → Digite o valor da coluna "Phone Number"
                
                Após preencher todos os campos, clique no botão "SUBMIT" para enviar o formulário.
                Repita este processo para TODOS os registros da planilha.
                
                O desafio estará concluído quando aparecer a mensagem "Congratulations" na tela.
                Procure por essa mensagem para confirmar que todos os registros foram processados com sucesso.
                Quando encontrar a mensagem "Congratulations", aguarde 5 segundos e finalize.
                ''',
            llm=llm,
            browser=self.browser,
            browser_context=self.context,
            controller=controller,
            max_actions_per_step=20,
            use_vision=True,
            max_failures=5,
            generate_gif=self.process_gif_path,
            save_playwright_script_path=str(self.process_script_path),
            source="webui",
        )
        
        # Executa o agente com retry e timeout
        try:
            process_history = await asyncio.wait_for(
                self.process_agent.run(max_steps=100),
                timeout=600
            )
        except asyncio.TimeoutError:
            logger.warning("Timeout no agente de processamento, tentando novamente...")
            process_history = await asyncio.wait_for(
                self.process_agent.run(max_steps=100),
                timeout=600
            )
            
        return process_history
    
    async def run_automation(self, llm, on_step_callback=None, on_done_callback=None):
        """
        Executa a automação completa do RPA Challenge
        
        Args:
            llm: Modelo de linguagem a ser usado
            on_step_callback: Callback para cada passo da execução
            on_done_callback: Callback para quando a execução terminar
            
        Returns:
            dict: Resultados da execução
        """
        result_lines = []
        download_history = None
        process_history = None
        
        try:
            # Executa o agente de download
            download_history = await self.run_download_agent(llm)
            
            if not download_history.is_done():
                error_msg = f"Falha ao baixar o arquivo Excel: {download_history.errors()}"
                result_lines.append(error_msg)
                raise Exception(error_msg)
            
            # Aguarda mais tempo para garantir que o download foi completamente concluído
            logger.info("Aguardando 10 segundos para garantir que o download foi completamente concluído...")
            await asyncio.sleep(10)
            
            # Tenta encontrar o arquivo Excel com retentativas
            excel_file = None
            for attempt in range(5):  # Aumentando o número de tentativas
                excel_file = find_latest_challenge_file()
                if excel_file:
                    # Verifica se o arquivo tem tamanho maior que zero
                    file_size = os.path.getsize(excel_file)
                    if file_size > 0:
                        logger.info(f"Arquivo Excel encontrado após tentativa {attempt+1}: {excel_file} (Tamanho: {file_size} bytes)")
                        # Verificar se o arquivo está completo
                        await asyncio.sleep(2)  # Aguarda um pouco mais para garantir que o arquivo esteja pronto
                        if file_size == os.path.getsize(excel_file):  # Se o tamanho não mudou, provavelmente está completo
                            break
                        else:
                            logger.info("Arquivo ainda está sendo baixado, aguardando...")
                    else:
                        logger.warning(f"Arquivo Excel encontrado, mas tem tamanho zero: {excel_file}")
                logger.warning(f"Arquivo Excel não válido na tentativa {attempt+1}, aguardando mais 5 segundos...")
                await asyncio.sleep(5)
                
            if not excel_file:
                error_msg = "Não foi possível encontrar o arquivo Excel após várias tentativas"
                result_lines.append(error_msg)
                raise Exception(error_msg)
            
            # Processa o arquivo Excel
            excel_data = await process_excel_data()
            
            # Executa o agente de processamento
            process_history = await self.run_process_agent(llm, excel_data)
            
            if not process_history.is_done():
                error_msg = f"Falha ao processar os dados do formulário: {process_history.errors()}"
                result_lines.append(error_msg)
                raise Exception(error_msg)
            
            # Gera resumo da execução
            result_lines.append("\n===== RESUMO FINAL DA EXECUÇÃO =====")
            
            if download_history:
                log_agent_history("Download Agent", download_history, result_lines)
            
            if process_history:
                log_agent_history("Process Agent", process_history, result_lines)
            
            # Salva o resumo em um arquivo txt
            with open(self.result_file, "w", encoding="utf-8") as f:
                f.write("\n".join(result_lines))
            
            # Chama o callback de conclusão
            if on_done_callback:
                on_done_callback({
                    "success": True,
                    "download_history": download_history,
                    "process_history": process_history,
                    "download_gif": self.download_gif_path if os.path.exists(self.download_gif_path) else None,
                    "process_gif": self.process_gif_path if os.path.exists(self.process_gif_path) else None,
                    "result_file": str(self.result_file),
                    "summary": "\n".join(result_lines)
                })
                
            return {
                "success": True,
                "download_history": download_history,
                "process_history": process_history,
                "download_gif": self.download_gif_path if os.path.exists(self.download_gif_path) else None,
                "process_gif": self.process_gif_path if os.path.exists(self.process_gif_path) else None,
                "result_file": str(self.result_file),
                "summary": "\n".join(result_lines)
            }
        
        except Exception as e:
            error_message = f"Erro durante a execução do RPA Challenge: {str(e)}"
            logger.error(error_message)
            result_lines.append(error_message)
            
            # Salva o resumo mesmo em caso de erro
            with open(self.result_file, "w", encoding="utf-8") as f:
                f.write("\n".join(result_lines))
            
            # Chama o callback de conclusão com erro
            if on_done_callback:
                on_done_callback({
                    "success": False,
                    "error": str(e),
                    "download_history": download_history,
                    "process_history": process_history,
                    "download_gif": self.download_gif_path if os.path.exists(self.download_gif_path) else None,
                    "process_gif": self.process_gif_path if os.path.exists(self.process_gif_path) else None,
                    "result_file": str(self.result_file),
                    "summary": "\n".join(result_lines)
                })
                
            return {
                "success": False,
                "error": str(e),
                "download_history": download_history,
                "process_history": process_history,
                "download_gif": self.download_gif_path if os.path.exists(self.download_gif_path) else None,
                "process_gif": self.process_gif_path if os.path.exists(self.process_gif_path) else None,
                "result_file": str(self.result_file),
                "summary": "\n".join(result_lines)
            }
        finally:
            # Garante que os recursos sejam fechados
            await self.close_resources() 