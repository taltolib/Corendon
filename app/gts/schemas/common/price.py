from pydantic import BaseModel

from app.gts.schemas.common.enums import PassengerType


class PriceInfo(BaseModel):
    price: float # Price + Обшое количество пасажиров
    currency: str # Name
    fee_amount: float #
    base_amount: float # BasePrice + Обшое количество пасажиров
    commission_amount: float #
    from_commission_amount: float #
    to_commission_amount: float #

class PriceDetail(BaseModel) :
    passenger_type : PassengerType #
    currency : str # Name
    quantity : int # 
    single_base_amount : float #BaseTotal
    single_tax_amount : float #TaxTotal
    single_tax_details : float #`TaxDetails`
    fee_amount : float #
    to_commission_amount :float #
    commission_amount : float #
    single_total_amount : float # BaseTotal + TaxTotal
    base_total_amount : float # BaseTotal + (зависеть  сколко пасаживов )
    tax_total_amount : float # TaxTotal + (зависеть  сколко пасаживов )
    total_amount : float # BaseTotal + TaxTotal + (зависеть  сколко пасаживов )
    payable_amount : float # BaseTotal + TaxTotal + (зависеть  сколко пасаживов ) = payable_amount
    single_fee_amount : float #
    single_service_fee_amount : float # ServiceCharge
    single_commission_amount : float #
    single_from_commission_amount : float #
    single_to_commission_amount : float #
    single_payable_amount : float # BaseTotal + TaxTotal
    service_fee_amount : float # ServiceCharge + (зависеть  сколко пасаживов )
    from_commission_amount : float #
    profit_commission_amount : float #



