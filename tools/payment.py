import aiohttp
import decimal
import hashlib
from urllib.parse import urlparse, parse_qs


def calculate_signature(*args) -> str:
    """Create signature MD5.
    """
    return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()


def parse_response(request: str) -> dict:
    """
    :param request: Link.
    :return: Dictionary.
    """
    params = parse_qs(urlparse(request).query)
    return {k: v[0] for k, v in params.items()}


async def check_signature_result(order_number: int,  # invoice number
                                 received_sum: decimal,  # cost of goods, RU
                                 received_signature: hex,  # SignatureValue
                                 password: str) -> bool:
    signature = calculate_signature(received_sum, order_number, password)
    if signature.lower() == received_signature.lower():
        return True
    return False


# Формирование URL переадресации пользователя на оплату.

async def generate_payment_link(
        merchant_login: str,  # Merchant login
        merchant_password_1: str,  # Merchant password
        cost: decimal,  # Cost of goods, RU
        number: int,  # Invoice number
        description: str,  # Description of the purchase
        is_test=0,
        robokassa_payment_url='https://auth.robokassa.ru/Merchant/Index.aspx', ) -> str:
    signature = calculate_signature(merchant_login, cost, number, merchant_password_1)

    data = {
        'MerchantLogin': merchant_login, 'OutSum': cost, 'InvId': number, 'Description': description, 'SignatureValue': signature, 'IsTest': is_test
        }
    async with aiohttp.ClientSession() as session:
        async with session.get(robokassa_payment_url, params=data) as resp:
            return str(resp.url)


# Получение уведомления об исполнении операции (ResultURL).

async def result_payment(merchant_password_2: str, request: str) -> str:
    """Verification of notification (ResultURL).
    :param request: HTTP parameters.
    """
    param_request = parse_response(request)
    cost = param_request['OutSum']
    number = param_request['InvId']
    signature = param_request['SignatureValue']

    if await check_signature_result(number, cost, signature, merchant_password_2):
        return f'OK{param_request["InvId"]}'
    return "bad sign"


# Проверка параметров в скрипте завершения операции (SuccessURL).

async def check_success_payment(
        merchant_password_1: str,
        request: str) -> str:
    """ Verification of operation parameters ("cashier check") in SuccessURL script.
    :param request: HTTP parameters
    """
    param_request = parse_response(request)
    cost = param_request['OutSum']
    number = param_request['InvId']
    signature = param_request['SignatureValue']

    if await check_signature_result(number, cost, signature, merchant_password_1):
        return "Thank you for using our service"
    return "bad sign"
