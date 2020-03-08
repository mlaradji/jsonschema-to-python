from typing import Union
from typing import TypedDict

class RootHi686922726f6f74Required(TypedDict, total=True):
    pass

class RootHi686922726f6f74Optional(TypedDict, total=False):
    hello: Union[float, int]
    pass

class RootHi686922726f6f74(RootHi686922726f6f74Required, RootHi686922726f6f74Optional):
    pass

class RootRequired(TypedDict, total=True):
    hi: RootHi686922726f6f74
    pass

class RootOptional(TypedDict, total=False):
    hello: Union[float, int]
    pass

class Root(RootRequired, RootOptional):
    pass

