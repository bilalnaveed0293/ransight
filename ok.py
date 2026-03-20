"""
Create synthetic test data based on known ransomware behavioral patterns.
Safe, legal, and effective for LSTM testing.
"""

import pandas as pd
import numpy as np

# Known behavioral signatures from ransomware families
RANSOMWARE_BEHAVIORS = {
    "wannacry": {
        "apis": [
            "CreateFileA", "CreateFileW", "WriteFile", "ReadFile",
            "FindFirstFileA", "FindFirstFileW", "FindNextFileA", "FindNextFileW",
            "DeleteFileA", "DeleteFileW", "SetFileAttributesA", "SetFileAttributesW",
            "CreateProcessA", "CreateProcessW", "ShellExecuteA", "ShellExecuteW",
            "RegOpenKeyExA", "RegOpenKeyExW", "RegSetValueExA", "RegSetValueExW",
            "GetVolumeInformationA", "GetVolumeInformationW", "GetDriveTypeA",
            "GetFileAttributesA", "GetFileAttributesW", "CryptEncrypt",
            "CryptDecrypt", "CryptGenKey", "GetSystemDirectoryA"
        ],
        "dlls": ["kernel32.dll", "ntdll.dll", "advapi32.dll", "wininet.dll", 
                 "cryptoapi.dll", "ole32.dll", "ws2_32.dll", "shell32.dll"]
    },
    
    "ryuk": {
        "apis": [
            "CreateRemoteThreadEx", "CreateRemoteThread", "OpenProcess",
            "ReadProcessMemory", "WriteProcessMemory", "VirtualAllocEx",
            "CreateFileA", "CreateFileW", "WriteFile", "CryptEncrypt",
            "RegOpenKeyExA", "RegSetValueExA", "CreateServiceA",
            "StartServiceA", "ControlService", "DeleteServiceA",
            "ShellExecuteA", "WinExec", "GetVolumeInformationA"
        ],
        "dlls": ["kernel32.dll", "ntdll.dll", "advapi32.dll", "wininet.dll",
                 "cryptoapi.dll", "shlwapi.dll", "shell32.dll"]
    },
    
    "conti": {
        "apis": [
            "CreateFileA", "WriteFile", "SetFilePointer", "ReadFile",
            "FindFirstFileA", "FindNextFileA", "DeleteFileA",
            "CreateProcessA", "ShellExecuteA", "WinExec",
            "RegOpenKeyExA", "RegSetValueExA", "RegDeleteValueA",
            "CryptEncrypt", "CryptGenKey", "GetVolumeInformationA",
            "GetLogicalDriveStringsA", "QueryDosDeviceA"
        ],
        "dlls": ["kernel32.dll", "ntdll.dll", "advapi32.dll", "cryptoapi.dll",
                 "shell32.dll", "ole32.dll", "wininet.dll"]
    },
    
    "lockbit": {
        "apis": [
            "CreateFileA", "CreateFileW", "WriteFile", "ReadFile",
            "CryptEncrypt", "CryptDecrypt", "CryptGenKey",
            "FindFirstFileA", "FindFirstFileW", "FindNextFileA",
            "DeleteFileA", "SetFileAttributesA", "CreateProcessA",
            "CreateRemoteThread", "OpenProcess", "VirtualAllocEx",
            "RegOpenKeyExA", "RegSetValueExA", "GetDriveTypeA"
        ],
        "dlls": ["kernel32.dll", "ntdll.dll", "advapi32.dll", "cryptoapi.dll",
                 "shell32.dll", "wininet.dll", "ole32.dll"]
    }
}

BENIGN_BEHAVIORS = {
    "legitimate_app": {
        "apis": [
            "CreateWindowExA", "GetMessageA", "TranslateMessage",
            "DispatchMessageA", "LoadLibraryA", "GetProcAddress",
            "SetWindowTextA", "GetWindowTextA", "CreateFontA",
            "TextOutA", "DrawTextA", "InvalidateRect",
            "malloc", "free", "memcpy", "strlen",
            "printf", "sprintf", "sscanf", "fopen", "fread", "fwrite"
        ],
        "dlls": ["user32.dll", "gdi32.dll", "kernel32.dll", "ole32.dll",
                 "advapi32.dll", "shell32.dll", "msvcrt.dll"]
    }
}


def create_lstm_test_dataset_from_behaviors():
    """
    Create a CSV dataset with realistic ransomware and benign behavioral signatures
    formatted for LSTM input.
    """
    
    samples = []
    
    # Create ransomware samples (400 total)
    for family, behavior in RANSOMWARE_BEHAVIORS.items():
        for sample_num in range(100):  # 100 per family
            row = {}
            
            # Create API call sequence (500 length)
            api_sequence = np.random.choice(behavior["apis"], size=500, replace=True)
            for idx, api in enumerate(api_sequence):
                row[f'ApiCall_{idx}'] = api
            
            # Create DLL sequence (10 length)
            dll_sequence = np.random.choice(behavior["dlls"], size=10, replace=True)
            for idx, dll in enumerate(dll_sequence):
                row[f'Dll_{idx}'] = dll
            
            row['Label'] = 1  # Ransomware
            row['Family'] = family.upper()
            samples.append(row)
    
    # Create benign samples (100 total)
    for sample_num in range(100):
        row = {}
        
        # Use legitimate behavior
        behavior = BENIGN_BEHAVIORS["legitimate_app"]
        
        # Create API call sequence (500 length)
        api_sequence = np.random.choice(behavior["apis"], size=500, replace=True)
        for idx, api in enumerate(api_sequence):
            row[f'ApiCall_{idx}'] = api
        
        # Create DLL sequence (10 length)
        dll_sequence = np.random.choice(behavior["dlls"], size=10, replace=True)
        for idx, dll in enumerate(dll_sequence):
            row[f'Dll_{idx}'] = dll
        
        row['Label'] = 0  # Benign
        row['Family'] = 'LEGITIMATE'
        samples.append(row)
    
    # Create DataFrame and save
    df = pd.DataFrame(samples)
    df.to_csv("lstm_test_dataset_behavioral.csv", index=False)
    
    print("✅ Dataset Created Successfully!")
    print(f"   Total samples: {len(df)}")
    print(f"   Ransomware: {len(df[df['Label'] == 1])}")
    print(f"   Benign: {len(df[df['Label'] == 0])}")
    print(f"\n   Ransomware families represented:")
    for family in df[df['Label'] == 1]['Family'].unique():
        count = len(df[df['Family'] == family])
        print(f"     - {family}: {count} samples")
    
    return df


if __name__ == "__main__":
    df = create_lstm_test_dataset_from_behaviors()