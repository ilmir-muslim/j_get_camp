from ninja import Schema


class BranchSchema(Schema):
    id: int
    name: str
    address: str
    city_id: int | None = None


class BranchCreateSchema(Schema):
    name: str
    address: str
    city_id: int | None = None
