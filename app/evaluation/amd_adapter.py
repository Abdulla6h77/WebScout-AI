"""Deliberately fail closed until the actual grader contract is provided."""


class AMDAdapter:
    def decode(self, payload):
        raise NotImplementedError("Official Match 4 input contract has not been supplied")

    def encode(self, answer):
        raise NotImplementedError("Official Match 4 output contract has not been supplied")
