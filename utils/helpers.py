# goldenkey_project/utils/helpers.py
import vnstock

def validate_symbols(symbols: list) -> (list, list):
    """
    Kiểm tra tính hợp lệ của danh sách các mã cổ phiếu.
    
    Returns:
        tuple: (danh_sách_hợp_lệ, danh_sách_không_hợp_lệ)
    """
    listing = vnstock.listing_companies(live=False)
    all_symbols = set(listing['ticker'])
    
    valid = []
    invalid = []
    
    for s in symbols:
        if s in all_symbols:
            valid.append(s)
        else:
            invalid.append(s)
            
    return valid, invalid