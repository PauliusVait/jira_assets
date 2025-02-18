import calendar
from datetime import datetime, date
from typing import Dict, Any, Optional
from decimal import Decimal, ROUND_HALF_UP

class DepreciationTable:
    """Complete depreciation table by device type and month"""
    RATES = [
        {"month": 1, "Computers": 63.75, "Tablets": 75.25, "Phones": 75.25},
        {"month": 2, "Computers": 61.00, "Tablets": 72.50, "Phones": 72.50},
        {"month": 3, "Computers": 58.25, "Tablets": 69.75, "Phones": 69.75},
        {"month": 4, "Computers": 55.50, "Tablets": 67.00, "Phones": 67.00},
        {"month": 5, "Computers": 52.75, "Tablets": 64.25, "Phones": 64.25},
        {"month": 6, "Computers": 50.00, "Tablets": 61.50, "Phones": 61.50},
        {"month": 7, "Computers": 47.25, "Tablets": 58.75, "Phones": 58.75},
        {"month": 8, "Computers": 44.50, "Tablets": 56.00, "Phones": 56.00},
        {"month": 9, "Computers": 41.75, "Tablets": 53.25, "Phones": 53.25},
        {"month": 10, "Computers": 39.00, "Tablets": 50.50, "Phones": 50.50},
        {"month": 11, "Computers": 36.25, "Tablets": 47.75, "Phones": 47.75},
        {"month": 12, "Computers": 35.00, "Tablets": 45.00, "Phones": 45.00},
        {"month": 13, "Computers": 34.25, "Tablets": 43.75, "Phones": 43.75},
        {"month": 14, "Computers": 33.50, "Tablets": 42.50, "Phones": 42.50},
        {"month": 15, "Computers": 32.75, "Tablets": 41.25, "Phones": 41.25},
        {"month": 16, "Computers": 32.00, "Tablets": 40.00, "Phones": 40.00},
        {"month": 17, "Computers": 31.25, "Tablets": 38.75, "Phones": 38.75},
        {"month": 18, "Computers": 30.50, "Tablets": 37.50, "Phones": 37.50},
        {"month": 19, "Computers": 29.75, "Tablets": 36.25, "Phones": 36.25},
        {"month": 20, "Computers": 29.00, "Tablets": 35.00, "Phones": 35.00},
        {"month": 21, "Computers": 28.25, "Tablets": 33.75, "Phones": 33.75},
        {"month": 22, "Computers": 27.50, "Tablets": 32.50, "Phones": 32.50},
        {"month": 23, "Computers": 26.75, "Tablets": 31.25, "Phones": 31.25},
        {"month": 24, "Computers": 26.00, "Tablets": 30.00, "Phones": 30.00},
        {"month": 25, "Computers": 25.59, "Tablets": 29.59, "Phones": 28.92},
        {"month": 26, "Computers": 25.18, "Tablets": 29.18, "Phones": 27.84},
        {"month": 27, "Computers": 24.77, "Tablets": 28.77, "Phones": 26.76},
        {"month": 28, "Computers": 24.36, "Tablets": 28.36, "Phones": 25.68},
        {"month": 29, "Computers": 23.95, "Tablets": 27.95, "Phones": 24.60},
        {"month": 30, "Computers": 23.54, "Tablets": 27.54, "Phones": 23.52},
        {"month": 31, "Computers": 23.13, "Tablets": 27.13, "Phones": 22.44},
        {"month": 32, "Computers": 22.72, "Tablets": 26.72, "Phones": 21.36},
        {"month": 33, "Computers": 22.31, "Tablets": 26.31, "Phones": 20.28},
        {"month": 34, "Computers": 21.90, "Tablets": 25.90, "Phones": 19.20},
        {"month": 35, "Computers": 21.49, "Tablets": 25.49, "Phones": 18.12},
        {"month": 36, "Computers": 21.00, "Tablets": 25.00, "Phones": 17.00},
        {"month": 37, "Computers": 20.10, "Tablets": 24.10, "Phones": 16.55},
        {"month": 38, "Computers": 19.20, "Tablets": 23.20, "Phones": 16.10},
        {"month": 39, "Computers": 18.30, "Tablets": 22.30, "Phones": 15.65},
        {"month": 40, "Computers": 17.40, "Tablets": 21.40, "Phones": 15.20},
        {"month": 41, "Computers": 16.50, "Tablets": 20.50, "Phones": 14.75},
        {"month": 42, "Computers": 15.60, "Tablets": 19.60, "Phones": 14.30},
        {"month": 43, "Computers": 14.70, "Tablets": 18.70, "Phones": 13.85},
        {"month": 44, "Computers": 13.80, "Tablets": 17.80, "Phones": 13.40},
        {"month": 45, "Computers": 12.90, "Tablets": 16.90, "Phones": 12.95},
        {"month": 46, "Computers": 12.00, "Tablets": 16.00, "Phones": 12.50},
        {"month": 47, "Computers": 11.10, "Tablets": 15.10, "Phones": 12.05},
        {"month": 48, "Computers": 10.20, "Tablets": 14.20, "Phones": 11.60}
    ]

class BuyoutCalculator:
    VAT_RATE = Decimal('0.21')  # 21% VAT rate
    MINIMUM_RATE = Decimal('0.102')  # 10.2% minimum rate for devices over 48 months

    @staticmethod
    def calculate_months_since_purchase(purchase_date: str) -> int:
        """
        Calculate exact months between purchase date and now, considering the day of the month
        """
        if not purchase_date:
            return 0
        
        purchase_dt = datetime.strptime(purchase_date, '%Y-%m-%d').date()
        today = date.today()
        
        # Calculate years and months difference
        years_diff = today.year - purchase_dt.year
        months_diff = today.month - purchase_dt.month
        
        # Total months
        total_months = years_diff * 12 + months_diff  # Fixed: using months_diff instead of undefined months
        
        # Adjust for day of the month
        if today.day < purchase_dt.day:
            # If we haven't reached the same day of the month, subtract one month
            total_months -= 1
            
        return max(1, total_months)

    @staticmethod
    def get_depreciation_rate(months: int, device_type: str = 'Computers') -> Decimal:
        """Get depreciation rate based on device age and type"""
        # Cap months at 48
        lookup_month = min(months, 48)
        
        # Find the rate for the given month and device type
        for rate in DepreciationTable.RATES:
            if rate['month'] == lookup_month:
                return Decimal(str(rate[device_type] / 100))  # Convert percentage to decimal
        
        # If beyond 48 months, use minimum rate
        return BuyoutCalculator.MINIMUM_RATE

    @classmethod
    def calculate_cost_with_vat(cls, original_cost: str) -> Optional[Decimal]:
        """Calculate cost with VAT"""
        if not original_cost:
            return None
            
        cost = Decimal(original_cost)
        vat_amount = cost * cls.VAT_RATE
        total = cost + vat_amount
        
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @classmethod
    def calculate_buyout_price(cls, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate buyout price and update asset with calculations"""
        if not asset.get('original_cost'):
            return asset

        # Calculate months since purchase
        months = cls.calculate_months_since_purchase(asset.get('purchase_date', ''))
        asset['age_months'] = months
        
        # Determine device type based on object_type_name
        device_type = 'Computers'  # Default to Computers
        if asset.get('object_type_name'):
            if 'tablet' in asset['object_type_name'].lower():
                device_type = 'Tablets'
            elif 'phone' in asset['object_type_name'].lower():
                device_type = 'Phones'
        asset['device_type'] = device_type
        
        # Always calculate cost with VAT
        cost_with_vat = cls.calculate_cost_with_vat(asset['original_cost'])
        if cost_with_vat:
            asset['cost_with_vat'] = str(cost_with_vat)
            
            # Get depreciation rate for specific month and device type
            rate = cls.get_depreciation_rate(months, device_type)
            asset['depreciation_rate'] = f"{rate * 100}%"
            
            # Calculate buyout price
            buyout_price = (cost_with_vat * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            asset['buyout_price'] = str(buyout_price)
            
        return asset

def update_asset_calculations(asset: Dict[str, Any]) -> Dict[str, Any]:
    """Update asset with calculated values"""
    return BuyoutCalculator.calculate_buyout_price(asset)
