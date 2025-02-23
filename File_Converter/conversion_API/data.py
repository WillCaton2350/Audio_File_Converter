from dataclasses import dataclass

@dataclass(frozen=True)
class states:
    api_key:str = '000000000000000000000000000000000000000000000000'
    base_url:str = "https://api.freeconvert.com/v1"
    upload_file_path:str = '/Users/administrator/Desktop/Projects/PyQt6Projects/File_Converter/conversion_API/mp3_files/example.mp3'
