"""
Data store for the kiosk.

Menu items are seeded in-memory. Orders are persisted in MongoDB; routers
only call the functions below, so the storage backend stays isolated here.
"""

from app import db
from app.models import MenuItem, Order, OrderCreate, OrderItemOut, OptionGroup, OptionChoice

_MENU: dict[str, MenuItem] = {}


def _seed_menu() -> None:
    items = [
        MenuItem(
            id="burger-classic",
            name="클래식 버거",
            category="버거",
            price=6500,
            description="순쇠고기 패티와 신선한 채소",
            emoji="🍔",
            option_groups=[
                OptionGroup(
                    name="사이즈",
                    required=True,
                    choices=[
                        OptionChoice(name="단품", price_delta=0),
                        OptionChoice(name="세트", price_delta=2500),
                    ],
                )
            ],
        ),
        MenuItem(
            id="burger-cheese",
            name="치즈 버거",
            category="버거",
            price=7000,
            description="고소한 체다치즈가 두 장",
            emoji="🧀",
            option_groups=[
                OptionGroup(
                    name="사이즈",
                    required=True,
                    choices=[
                        OptionChoice(name="단품", price_delta=0),
                        OptionChoice(name="세트", price_delta=2500),
                    ],
                )
            ],
        ),
        MenuItem(
            id="burger-spicy",
            name="스파이시 치킨 버거",
            category="버거",
            price=7200,
            description="매콤한 치킨 패티",
            emoji="🌶️",
            option_groups=[
                OptionGroup(
                    name="맵기",
                    required=True,
                    choices=[
                        OptionChoice(name="보통맛", price_delta=0),
                        OptionChoice(name="매운맛", price_delta=0),
                    ],
                ),
                OptionGroup(
                    name="사이즈",
                    required=True,
                    choices=[
                        OptionChoice(name="단품", price_delta=0),
                        OptionChoice(name="세트", price_delta=2500),
                    ],
                ),
            ],
        ),
        MenuItem(
            id="side-fries",
            name="감자튀김",
            category="사이드",
            price=3000,
            description="바삭한 감자튀김",
            emoji="🍟",
            option_groups=[
                OptionGroup(
                    name="사이즈",
                    required=True,
                    choices=[
                        OptionChoice(name="레귤러", price_delta=0),
                        OptionChoice(name="라지", price_delta=1000),
                    ],
                )
            ],
        ),
        MenuItem(
            id="side-nuggets",
            name="치킨너겟 (6pc)",
            category="사이드",
            price=4000,
            description="바삭한 너겟 6조각",
            emoji="🍗",
        ),
        MenuItem(
            id="drink-cola",
            name="콜라",
            category="음료",
            price=2000,
            description="시원한 탄산음료",
            emoji="🥤",
            option_groups=[
                OptionGroup(
                    name="사이즈",
                    required=True,
                    choices=[
                        OptionChoice(name="레귤러", price_delta=0),
                        OptionChoice(name="라지", price_delta=500),
                    ],
                )
            ],
        ),
        MenuItem(
            id="drink-coffee",
            name="아메리카노",
            category="음료",
            price=2500,
            description="깊은 풍미의 커피",
            emoji="☕",
            option_groups=[
                OptionGroup(
                    name="온도",
                    required=True,
                    choices=[
                        OptionChoice(name="ICE", price_delta=0),
                        OptionChoice(name="HOT", price_delta=0),
                    ],
                )
            ],
        ),
        MenuItem(
            id="dessert-icecream",
            name="소프트 아이스크림",
            category="디저트",
            price=2000,
            description="부드러운 바닐라 아이스크림",
            emoji="🍦",
        ),
        MenuItem(
            id="special-item",
            name="태이나르도 윤카프린스",
            category="스페셜",
            price=100_000_000,
            description="단 하나뿐인 한정 상품",
            emoji="✨",
            image_url="/static/img/special-item.jpg",
            stock=1,
        ),
        MenuItem(
            id="dessert-churros",
            name="츄러스",
            category="디저트",
            price=3500,
            description="시나몬 슈가 츄러스",
            emoji="🥨",
            sold_out=True,
        ),
    ]
    for item in items:
        _MENU[item.id] = item


_seed_menu()


def get_categories() -> list[str]:
    seen: list[str] = []
    for item in _MENU.values():
        if item.category not in seen:
            seen.append(item.category)
    return seen


def get_menu_items() -> list[MenuItem]:
    return list(_MENU.values())


def get_menu_item(menu_item_id: str) -> MenuItem | None:
    return _MENU.get(menu_item_id)


def create_order(order_in: OrderCreate) -> Order:
    out_items: list[OrderItemOut] = []
    stock_updates: list[tuple[MenuItem, int]] = []
    total = 0

    for line in order_in.items:
        menu_item = get_menu_item(line.menu_item_id)
        if menu_item is None:
            raise ValueError(f"알 수 없는 메뉴입니다: {line.menu_item_id}")
        if menu_item.sold_out:
            raise ValueError(f"품절된 메뉴입니다: {menu_item.name}")
        if line.quantity < 1:
            raise ValueError("수량은 1개 이상이어야 합니다.")
        if menu_item.stock is not None and line.quantity > menu_item.stock:
            raise ValueError(f"재고가 부족합니다: {menu_item.name} (남은 수량 {menu_item.stock}개)")

        unit_price = menu_item.price
        option_group_map = {g.name: g for g in menu_item.option_groups}
        for selected in line.selected_options:
            group = option_group_map.get(selected.group_name)
            if group is None:
                raise ValueError(f"잘못된 옵션입니다: {selected.group_name}")
            choice = next((c for c in group.choices if c.name == selected.choice_name), None)
            if choice is None:
                raise ValueError(f"잘못된 옵션 값입니다: {selected.choice_name}")
            unit_price += choice.price_delta

        required_groups = {g.name for g in menu_item.option_groups if g.required}
        selected_groups = {s.group_name for s in line.selected_options}
        missing = required_groups - selected_groups
        if missing:
            raise ValueError(f"{menu_item.name}: 필수 옵션을 선택해주세요 ({', '.join(missing)})")

        line_total = unit_price * line.quantity
        total += line_total
        out_items.append(
            OrderItemOut(
                menu_item_id=menu_item.id,
                name=menu_item.name,
                quantity=line.quantity,
                unit_price=unit_price,
                selected_options=line.selected_options,
                line_total=line_total,
            )
        )
        stock_updates.append((menu_item, line.quantity))

    for menu_item, quantity in stock_updates:
        if menu_item.stock is None:
            continue
        menu_item.stock -= quantity
        if menu_item.stock <= 0:
            menu_item.sold_out = True

    order = Order(
        id=f"order-{db.next_sequence('order_id')}",
        pickup_number=db.next_sequence("pickup_number"),
        items=out_items,
        order_type=order_in.order_type,
        total_price=total,
    )
    doc = order.model_dump()
    doc["_id"] = doc.pop("id")
    db.orders_collection.insert_one(doc)
    return order


def get_order(order_id: str) -> Order | None:
    doc = db.orders_collection.find_one({"_id": order_id})
    if doc is None:
        return None
    doc = dict(doc)
    doc["id"] = doc.pop("_id")
    return Order.model_validate(doc)
