"""
Configuração e inicialização do Laminar para observabilidade e rastreamento
"""
import os
import logging
from typing import Optional, Dict, Any
from lmnr import Laminar, observe
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

logger = logging.getLogger(__name__)

class LaminarConfig:
    """Classe para gerenciar a configuração do Laminar"""
    
    def __init__(self):
        self.project_api_key = os.getenv('LMNR_PROJECT_API_KEY')
        self.base_url = os.getenv('LMNR_BASE_URL', 'https://api.lmnr.ai')
        self.enabled = os.getenv('LMNR_ENABLED', 'true').lower() == 'true'
        self.initialized = False
        
    def initialize(self) -> bool:
        """Inicializa o Laminar se estiver habilitado"""
        if not self.enabled:
            logger.info("Laminar está desabilitado")
            return False
            
        if not self.project_api_key:
            logger.warning("LMNR_PROJECT_API_KEY não encontrada. Laminar não será inicializado.")
            return False
            
        try:
            Laminar.initialize(
                project_api_key=self.project_api_key,
                base_url=self.base_url
            )
            self.initialized = True
            logger.info(f"Laminar inicializado com sucesso - Base URL: {self.base_url}")
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar Laminar: {e}")
            return False
    
    def is_enabled(self) -> bool:
        """Verifica se o Laminar está habilitado e inicializado"""
        return self.enabled and self.initialized

# Instância global
laminar_config = LaminarConfig()

def init_laminar() -> bool:
    """Função para inicializar o Laminar"""
    return laminar_config.initialize()

def is_laminar_enabled() -> bool:
    """Verifica se o Laminar está habilitado"""
    return laminar_config.is_enabled()

# Decorator personalizado para observabilidade
def observe_task(name: str = None, metadata: Dict[str, Any] = None):
    """
    Decorator personalizado para observar tarefas do agente
    
    Args:
        name: Nome da tarefa
        metadata: Metadados adicionais
    """
    def decorator(func):
        if not is_laminar_enabled():
            return func
            
        return observe(name=name or func.__name__, metadata=metadata or {})(func)
    
    return decorator

def log_metric(name: str, value: Any, metadata: Dict[str, Any] = None):
    """
    Log de métricas personalizadas
    
    Args:
        name: Nome da métrica
        value: Valor da métrica
        metadata: Metadados adicionais
    """
    if not is_laminar_enabled():
        return
        
    try:
        # Aqui você pode implementar logging de métricas customizadas
        logger.info(f"Métrica {name}: {value}")
        if metadata:
            logger.info(f"Metadados: {metadata}")
    except Exception as e:
        logger.error(f"Erro ao registrar métrica {name}: {e}")

def trace_browser_action(action_type: str, element: str = None, success: bool = True, 
                        duration: float = None, error: str = None):
    """
    Rastreia ações do navegador
    
    Args:
        action_type: Tipo de ação (click, type, navigate, etc.)
        element: Elemento alvo
        success: Se a ação foi bem-sucedida
        duration: Duração da ação
        error: Mensagem de erro se houver
    """
    if not is_laminar_enabled():
        return
        
    metadata = {
        "action_type": action_type,
        "element": element,
        "success": success,
        "duration": duration,
        "error": error
    }
    
    log_metric("browser_action", action_type, metadata) 