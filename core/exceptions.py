from rest_framework.exceptions import APIException

class ValidationError(APIException):
    status_code = 400
    default_detail = 'Dados inválidos'
    default_code = 'validation_error'