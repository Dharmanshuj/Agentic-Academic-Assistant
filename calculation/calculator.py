from pydantic import validate_call

@validate_call
def calculate_prorated_salary(base_salary: float, total_days: int, present_days: int) -> dict:
    """
    Performs the exact payroll calculation. 
    Logic: Base * (Present / Total)
    """
    if total_days <= 0:
        return {"error": "Total days must be greater than zero."}
    
    # Precise calculation
    amount = base_salary * (present_days / total_days)
    
    return {
        "amount": round(amount, 2),
        "formula": f"{base_salary} * ({present_days}/{total_days})",
        "breakdown": {
            "monthly_base": base_salary,
            "days_in_month": total_days,
            "days_active": present_days
        }
    }