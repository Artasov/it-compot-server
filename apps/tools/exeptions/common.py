from rest_framework import status
from rest_framework.exceptions import APIException


class UnitAlreadyFullException(BaseException):
    pass


class NoSlotCodeFormingUnitException(BaseException):
    pass


class NotFoundCourseUnitBySlotCodeException(BaseException):
    pass


class PaymentException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Произошла ошибка при добавлении платежа.'
    default_code = 'error_adding_payment'
