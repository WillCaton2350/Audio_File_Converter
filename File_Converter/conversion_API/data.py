from dataclasses import dataclass
from datetime import datetime
from time import sleep

@dataclass(frozen=True)
class states:
    api_key:str = 'api_production_154b8c93db3571ddb087e3bd4b57b85b799704bba9051b59633592bd2796c3f1.67bab0d3d6cf59b2c9a65b62.67bab0e4a5fd01cc937cb1cc'
    base_url:str = "https://api.freeconvert.com/v1"
    for i in range(1):
        var = datetime.now()
    file_name: str = f'example_file ({var})'

class time_altered:
    time_buffer = sleep
    
class Credit:
    """FreeConverterApi"""
