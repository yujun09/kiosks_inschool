from pydantic import BaseModel


class OptionChoice(BaseModel):
    name: str
    price_delta: int = 0


class OptionGroup(BaseModel):
    name: str
    required: bool = False
    choices: list[OptionChoice]


class MenuItem(BaseModel):
    id: str
    name: str
    category: str
    price: int
    description: str = ""
    emoji: str = "🍽️"
    image_url: str | None = None
    sold_out: bool = False
    stock: int | None = None
    option_groups: list[OptionGroup] = []


class SelectedOption(BaseModel):
    group_name: str
    choice_name: str


class OrderItemIn(BaseModel):
    menu_item_id: str
    quantity: int
    selected_options: list[SelectedOption] = []


class OrderCreate(BaseModel):
    items: list[OrderItemIn]
    order_type: str = "takeout"  # "takeout" or "dine_in"


class OrderItemOut(BaseModel):
    menu_item_id: str
    name: str
    quantity: int
    unit_price: int
    selected_options: list[SelectedOption] = []
    line_total: int


class Order(BaseModel):
    id: str
    pickup_number: int
    items: list[OrderItemOut]
    order_type: str
    total_price: int
    status: str = "received"
