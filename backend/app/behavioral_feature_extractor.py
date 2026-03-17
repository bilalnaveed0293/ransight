import pefile
from collections import OrderedDict
from typing import Dict, List
import numpy as np


def _extract_api_calls(pe_path: str) -> List[str]:
    """
    Extract imported API functions from PE file.
    
    Returns a list of API call names in order of appearance.
    Pads with "PAD" or truncates to max 500 APIs.
    """
    try:
        pe = pefile.PE(pe_path)
    except Exception as e:
        print(f"Warning: Could not parse PE file: {e}")
        return ["PAD"] * 500
    
    api_calls = []
    
    try:
        if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
            for entry in pe.DIRECTORY_ENTRY_IMPORT:
                if hasattr(entry, 'imports'):
                    for imp in entry.imports:
                        if hasattr(imp, 'name') and imp.name:
                            api_name = imp.name.decode('utf-8', errors='ignore')
                            api_calls.append(api_name)
    except Exception as e:
        print(f"Warning: Error extracting API calls: {e}")
    
    # Pad or truncate to exactly 500
    if len(api_calls) < 500:
        api_calls.extend(["PAD"] * (500 - len(api_calls)))
    else:
        api_calls = api_calls[:500]
    
    return api_calls


def _extract_dll_imports(pe_path: str) -> List[str]:
    """
    Extract imported DLL names from PE file.
    
    Returns a list of DLL names in order of appearance.
    Pads with "PAD" or truncates to max 10 DLLs.
    """
    try:
        pe = pefile.PE(pe_path)
    except Exception as e:
        print(f"Warning: Could not parse PE file: {e}")
        return ["PAD"] * 10
    
    dlls = []
    
    try:
        if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
            for entry in pe.DIRECTORY_ENTRY_IMPORT:
                dll_name = entry.dll.decode('utf-8', errors='ignore')
                dlls.append(dll_name)
    except Exception as e:
        print(f"Warning: Error extracting DLLs: {e}")
    
    # Pad or truncate to exactly 10
    if len(dlls) < 10:
        dlls.extend(["PAD"] * (10 - len(dlls)))
    else:
        dlls = dlls[:10]
    
    return dlls


def extract_behavioral_features(file_path: str) -> Dict[str, List]:
    """
    Extract behavioral features from a PE file.
    
    Returns a dictionary with:
      - 'api_calls': List[str] of length 500
      - 'dlls': List[str] of length 10
    """
    api_calls = _extract_api_calls(file_path)
    dlls = _extract_dll_imports(file_path)
    
    return {
        'api_calls': api_calls,
        'dlls': dlls
    }


def format_behavioral_features_for_lstm(features: Dict[str, List]) -> Dict[str, any]:
    """
    Format extracted behavioral features into the exact format expected by LSTM.
    
    Converts the dictionary into flat feature vector with columns:
      ApiCall_0, ApiCall_1, ..., ApiCall_499
      Dll_0, Dll_1, ..., Dll_9
    
    Returns a dictionary that maps to a pandas DataFrame for LSTM prediction.
    """
    formatted = {}
    
    # Add API calls
    for i, api in enumerate(features['api_calls']):
        formatted[f'ApiCall_{i}'] = api
    
    # Add DLLs
    for i, dll in enumerate(features['dlls']):
        formatted[f'Dll_{i}'] = dll
    
    return formatted