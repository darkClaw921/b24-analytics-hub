"""
Safe Python code executor for dashboard charts
"""
import json
import sys
import io
import contextlib
from typing import Dict, Any, Optional
from RestrictedPython import compile_restricted, safe_globals
from RestrictedPython.Guards import safe_builtins
from RestrictedPython.PrintCollector import PrintCollector
import logging

logger = logging.getLogger(__name__)


class CodeExecutor:
    """Safe executor for Python code with restrictions"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        
        # Разрешенные встроенные функции
        self.allowed_builtins = {
            'abs', 'all', 'any', 'bool', 'dict', 'enumerate', 'float', 'int',
            'isinstance', 'len', 'list', 'max', 'min', 'range', 'round', 'set',
            'sorted', 'str', 'sum', 'tuple', 'zip', 'print', 'json'
        }
        
        # Безопасные глобальные переменные
        self.safe_globals_dict = safe_globals.copy()
        safe_builtins_dict = {
            k: v for k, v in safe_builtins.items() 
            if k in self.allowed_builtins
        }
        
        # Добавляем безопасный __import__ для импорта только json
        def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == 'json':
                import json as json_module
                return json_module
            raise ImportError(f"Import of '{name}' is not allowed")
        
        safe_builtins_dict['__import__'] = safe_import
        self.safe_globals_dict['__builtins__'] = safe_builtins_dict
        
        # Добавляем json модуль
        import json as json_module
        self.safe_globals_dict['json'] = json_module
        # Добавляем необходимые функции для RestrictedPython
        self.safe_globals_dict['_print_'] = PrintCollector
        self.safe_globals_dict['_getattr_'] = getattr
    
    def execute(self, code: str) -> Dict[str, Any]:
        """
        Выполняет Python код в безопасном окружении
        
        Args:
            code: Python код для выполнения
            
        Returns:
            Dict с результатом выполнения или ошибкой
        """
        try:
            # Компиляция кода с ограничениями
            compile_result = compile_restricted(code, '<inline>', 'exec')
            
            # Проверка типа результата - может быть объект кода или CompileResult
            if hasattr(compile_result, 'errors') and compile_result.errors:
                return {
                    "success": False,
                    "error": f"Compilation errors: {', '.join(compile_result.errors)}"
                }
            
            # Получаем объект кода
            if hasattr(compile_result, 'code'):
                byte_code = compile_result.code
            else:
                byte_code = compile_result
            
            # Захват stdout
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            # Локальные переменные для выполнения
            local_vars = {}
            
            # Выполнение кода
            with contextlib.redirect_stdout(stdout_capture), \
                 contextlib.redirect_stderr(stderr_capture):
                exec(byte_code, self.safe_globals_dict, local_vars)
            
            # Получение вывода
            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()
            
            if stderr_output:
                return {
                    "success": False,
                    "error": f"Execution error: {stderr_output}"
                }
            
            # Проверяем переменную 'printed' (используется RestrictedPython для print)
            printed_output = None
            if 'printed' in local_vars:
                printed_output = str(local_vars['printed']).strip()
            
            # Парсинг JSON из stdout или printed
            output_to_parse = printed_output if printed_output else stdout_output
            
            if output_to_parse:
                try:
                    result = json.loads(output_to_parse)
                    return {
                        "success": True,
                        "data": result
                    }
                except json.JSONDecodeError:
                    # Если не JSON, проверяем локальные переменные
                    if 'result' in local_vars:
                        result = local_vars['result']
                        if isinstance(result, dict):
                            return {
                                "success": True,
                                "data": result
                            }
                    
                    return {
                        "success": False,
                        "error": f"Output is not valid JSON. Output: {output_to_parse[:200]}"
                    }
            else:
                # Проверяем локальные переменные
                if 'result' in local_vars:
                    result = local_vars['result']
                    if isinstance(result, dict):
                        return {
                            "success": True,
                            "data": result
                        }
                
                return {
                    "success": False,
                    "error": "No output or result variable found. Code should print JSON or set 'result' variable."
                }
                
        except Exception as e:
            logger.error(f"Error executing code: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}"
            }


# Глобальный экземпляр executor
executor = CodeExecutor()

