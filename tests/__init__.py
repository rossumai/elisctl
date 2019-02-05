from collections import UserDict


class SuperDictOf(UserDict):
    def __eq__(self, other):
        if not isinstance(other, dict):
            return False

        for k, v in self.items():
            if k not in other or v != other[k]:
                return False

        return True

    def __repr__(self):
        return f"SuperDictOf({super().__repr__()})"
