const state = {
  menuItems: [],
  categories: [],
  activeCategory: null,
  orderType: "takeout",
  cart: [], // { cartLineId, menuItemId, name, unitPrice, quantity, selectedOptions: [{group_name, choice_name}] }
};

let cartLineSeq = 1;
let pendingItem = null; // menu item currently open in the option modal
let pendingSelections = {}; // group_name -> choice_name
let pendingQty = 1;

const el = (id) => document.getElementById(id);

function formatWon(n) {
  return n.toLocaleString("ko-KR") + "원";
}

function showToast(message) {
  const toast = el("toast");
  toast.textContent = message;
  toast.classList.remove("hidden");
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => toast.classList.add("hidden"), 2200);
}

async function loadMenu() {
  const [itemsRes, categoriesRes] = await Promise.all([
    fetch("/api/menu"),
    fetch("/api/menu/categories"),
  ]);
  state.menuItems = await itemsRes.json();
  state.categories = await categoriesRes.json();
  state.activeCategory = state.categories[0] ?? null;
  renderCategoryTabs();
  renderMenuGrid();
}

function renderCategoryTabs() {
  const nav = el("category-tabs");
  nav.innerHTML = "";
  for (const category of state.categories) {
    const btn = document.createElement("button");
    btn.className = "category-tab" + (category === state.activeCategory ? " active" : "");
    btn.textContent = category;
    btn.addEventListener("click", () => {
      state.activeCategory = category;
      renderCategoryTabs();
      renderMenuGrid();
    });
    nav.appendChild(btn);
  }
}

function renderMenuGrid() {
  const grid = el("menu-grid");
  grid.innerHTML = "";
  const items = state.menuItems.filter((item) => item.category === state.activeCategory);
  for (const item of items) {
    const card = document.createElement("button");
    card.className = "menu-card" + (item.sold_out ? " sold-out" : "");
    card.disabled = item.sold_out;
    const media = item.image_url
      ? `<img class="item-image" src="${item.image_url}" alt="${item.name}" />`
      : `<span class="emoji">${item.emoji}</span>`;
    card.innerHTML = `
      ${media}
      <div class="name">${item.name}</div>
      <div class="desc">${item.description}</div>
      <div class="price">${formatWon(item.price)}</div>
      ${item.sold_out ? '<span class="sold-out-badge">품절</span>' : ""}
    `;
    card.addEventListener("click", () => openItem(item));
    grid.appendChild(card);
  }
}

function openItem(item) {
  if (item.sold_out) return;
  if (item.option_groups.length === 0) {
    addToCart(item, [], 1);
    showToast(`${item.name} 담았습니다`);
    return;
  }
  pendingItem = item;
  pendingSelections = {};
  pendingQty = 1;
  for (const group of item.option_groups) {
    if (group.required && group.choices.length > 0) {
      pendingSelections[group.name] = group.choices[0].name;
    }
  }
  renderOptionModal();
  el("option-modal").classList.remove("hidden");
}

function renderOptionModal() {
  el("option-modal-title").textContent = pendingItem.name;
  el("option-modal-desc").textContent = pendingItem.description;
  el("qty-value").textContent = pendingQty;

  const container = el("option-modal-groups");
  container.innerHTML = "";
  for (const group of pendingItem.option_groups) {
    const groupDiv = document.createElement("div");
    groupDiv.className = "option-group";
    const title = document.createElement("div");
    title.className = "option-group-title";
    title.textContent = group.name + (group.required ? " (필수)" : "");
    groupDiv.appendChild(title);

    const row = document.createElement("div");
    row.className = "option-choice-row";
    for (const choice of group.choices) {
      const btn = document.createElement("button");
      const selected = pendingSelections[group.name] === choice.name;
      btn.className = "option-choice-btn" + (selected ? " selected" : "");
      btn.textContent = choice.name + (choice.price_delta ? ` (+${formatWon(choice.price_delta)})` : "");
      btn.addEventListener("click", () => {
        pendingSelections[group.name] = choice.name;
        renderOptionModal();
      });
      row.appendChild(btn);
    }
    groupDiv.appendChild(row);
    container.appendChild(groupDiv);
  }
}

function closeOptionModal() {
  el("option-modal").classList.add("hidden");
  pendingItem = null;
}

el("qty-minus").addEventListener("click", () => {
  pendingQty = Math.max(1, pendingQty - 1);
  el("qty-value").textContent = pendingQty;
});

el("qty-plus").addEventListener("click", () => {
  pendingQty = Math.min(20, pendingQty + 1);
  el("qty-value").textContent = pendingQty;
});

el("option-cancel-btn").addEventListener("click", closeOptionModal);

el("option-add-btn").addEventListener("click", () => {
  const missing = pendingItem.option_groups.filter(
    (g) => g.required && !pendingSelections[g.name]
  );
  if (missing.length > 0) {
    showToast("필수 옵션을 선택해주세요");
    return;
  }
  const selectedOptions = Object.entries(pendingSelections).map(([group_name, choice_name]) => ({
    group_name,
    choice_name,
  }));
  addToCart(pendingItem, selectedOptions, pendingQty);
  showToast(`${pendingItem.name} 담았습니다`);
  closeOptionModal();
});

function unitPriceFor(item, selectedOptions) {
  let price = item.price;
  for (const sel of selectedOptions) {
    const group = item.option_groups.find((g) => g.name === sel.group_name);
    const choice = group?.choices.find((c) => c.name === sel.choice_name);
    if (choice) price += choice.price_delta;
  }
  return price;
}

function addToCart(item, selectedOptions, quantity) {
  state.cart.push({
    cartLineId: cartLineSeq++,
    menuItemId: item.id,
    name: item.name,
    unitPrice: unitPriceFor(item, selectedOptions),
    quantity,
    selectedOptions,
  });
  renderCart();
}

function renderCart() {
  const container = el("cart-items");
  container.innerHTML = "";

  if (state.cart.length === 0) {
    container.innerHTML = '<div class="cart-empty">담긴 메뉴가 없습니다</div>';
  }

  let total = 0;
  for (const line of state.cart) {
    const lineTotal = line.unitPrice * line.quantity;
    total += lineTotal;

    const div = document.createElement("div");
    div.className = "cart-item";
    const optionsText = line.selectedOptions.map((o) => o.choice_name).join(" / ");
    div.innerHTML = `
      <div class="cart-item-top">
        <div>
          <div class="cart-item-name">${line.name}</div>
          ${optionsText ? `<div class="cart-item-options">${optionsText}</div>` : ""}
        </div>
        <button class="cart-item-remove" aria-label="삭제">✕</button>
      </div>
      <div class="cart-item-bottom">
        <div class="cart-qty-control">
          <button class="minus">-</button>
          <span>${line.quantity}</span>
          <button class="plus">+</button>
        </div>
        <div class="cart-item-price">${formatWon(lineTotal)}</div>
      </div>
    `;
    div.querySelector(".cart-item-remove").addEventListener("click", () => {
      state.cart = state.cart.filter((l) => l.cartLineId !== line.cartLineId);
      renderCart();
    });
    div.querySelector(".minus").addEventListener("click", () => {
      line.quantity = Math.max(1, line.quantity - 1);
      renderCart();
    });
    div.querySelector(".plus").addEventListener("click", () => {
      line.quantity = Math.min(20, line.quantity + 1);
      renderCart();
    });
    container.appendChild(div);
  }

  el("cart-total-price").textContent = formatWon(total);
  el("checkout-btn").disabled = state.cart.length === 0;
}

el("clear-cart-btn").addEventListener("click", () => {
  state.cart = [];
  renderCart();
});

document.querySelectorAll(".order-type-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".order-type-btn").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    state.orderType = btn.dataset.type;
  });
});

el("checkout-btn").addEventListener("click", async () => {
  if (state.cart.length === 0) return;
  const payload = {
    order_type: state.orderType,
    items: state.cart.map((line) => ({
      menu_item_id: line.menuItemId,
      quantity: line.quantity,
      selected_options: line.selectedOptions,
    })),
  };

  el("checkout-btn").disabled = true;
  try {
    const res = await fetch("/api/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      showToast(err.detail || "주문에 실패했습니다");
      el("checkout-btn").disabled = false;
      return;
    }
    const order = await res.json();
    el("pickup-number").textContent = order.pickup_number;
    el("complete-modal").classList.remove("hidden");
  } catch (e) {
    showToast("네트워크 오류가 발생했습니다");
    el("checkout-btn").disabled = false;
  }
});

el("new-order-btn").addEventListener("click", () => {
  state.cart = [];
  renderCart();
  el("complete-modal").classList.add("hidden");
});

loadMenu();
