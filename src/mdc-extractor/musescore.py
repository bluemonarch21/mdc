import dataclasses

@dataclasses.dataclass
class Score:
    version: str  # 
    arranger: str
    composer: str #
    creationDate: str
    movementNumber: str
    movementTitle: str
    source: str
    workNumber: str
    workTitle: str
    parts: list[Part]

# instrumentId = [keyboard, piano, grand piano, organ]
@dataclasses.dataclass
class Part:
    instrumentId: str 
    trackName: str
    longName: str
    shortName: str



def extract_feature(filename: str) -> Feature:
    pass

if __name__ == "__main__":