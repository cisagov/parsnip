# Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

import utils

class CustomType:
    def __init__(self, name, interpretingFunction, returnType):
        self.name = name
        self.interpretingFunction = interpretingFunction
        self.returnType = returnType
