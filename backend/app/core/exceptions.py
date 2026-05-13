
#region Интеграционные исключения
class IntegrationError(Exception):
  def __init__(self, message: str, service: str):
    super().__init__(message)
    self.service = service

# Обрыв сети, недоступность хоста
class IntegrationConnectionError(IntegrationError):
  pass

# Превышение лимита ожидания ответа
class IntegrationTimeoutError(IntegrationError): 
  pass

# Ошибки валидации, авторизации, внутренней логики внешнего API
class IntegrationServiceError(IntegrationError):  
  pass

