/**
 * Логика витрины «Дежкино», фильтрации, корзины и интеграции с Telegram
 */

// Инициализация Telegram WebApp (если запущено внутри Telegram)
const tg = window.Telegram?.WebApp;
if (tg) {
  try {
    tg.ready();
    tg.expand();
    document.body.classList.add("in-telegram");
    if (tg.colorScheme === "dark" || window.matchMedia?.("(prefers-color-scheme: dark)").matches) {
      document.body.classList.add("dark-theme");
    }
  } catch (e) {
    console.log("Telegram WebApp context initialized in standalone mode");
  }
}

// Состояние приложения
let liveProducts = (typeof PRODUCTS !== "undefined") ? PRODUCTS : [];

const state = {
  activeCategory: "all",
  cart: {} // { [productId]: quantity }
};

// Загрузка живых данных товаров (с поддержкой localStorage для GitHub Pages и API для локального сервера)
async function fetchLiveProducts() {
  // 1. Сначала проверяем изменения из панели управления в localStorage
  try {
    const cached = localStorage.getItem("dezhkino_products");
    if (cached) {
      const parsed = JSON.parse(cached);
      if (Array.isArray(parsed) && parsed.length > 0) {
        liveProducts = parsed;
        renderProducts();
        updateCartUI();
      }
    }
  } catch (e) {}

  // 2. Если есть бэкенд-сервер, подтягиваем данные через API
  try {
    const res = await fetch("/api/products");
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        liveProducts = data;
        renderProducts();
        updateCartUI();
      }
    }
  } catch (err) {
    console.log("Локальный fallback: активен актуальный каталог");
  }
}

// DOM Элементы
const categoriesContainer = document.getElementById("categoriesNav");
const productsContainer = document.getElementById("productsGrid");
const cartBadge = document.getElementById("headerCartCount");
const stickyCartBar = document.getElementById("stickyCartBar");
const stickyCartItems = document.getElementById("stickyCartItems");
const stickyCartTotal = document.getElementById("stickyCartTotal");
const cartModal = document.getElementById("cartModal");
const cartItemsList = document.getElementById("cartItemsList");
const cartModalTotal = document.getElementById("cartModalTotal");
const checkoutForm = document.getElementById("checkoutForm");

// Рендер кнопок категорий
function renderCategories() {
  if (!categoriesContainer) return;
  categoriesContainer.innerHTML = CATEGORIES.map(cat => `
    <button class="category-btn ${cat.id === state.activeCategory ? 'active' : ''}" data-cat="${cat.id}">
      ${cat.name}
    </button>
  `).join("");

  categoriesContainer.querySelectorAll(".category-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      state.activeCategory = btn.dataset.cat;
      renderCategories();
      renderProducts();
    });
  });
}

// Рендер карточек товаров
function renderProducts() {
  if (!productsContainer) return;
  
  const filtered = state.activeCategory === "all" 
    ? liveProducts 
    : liveProducts.filter(p => p.category === state.activeCategory);

  productsContainer.innerHTML = filtered.map((p, idx) => {
    const qty = state.cart[p.id] || 0;
    const inStock = p.inStock !== false;
    const delayClass = `reveal-delay-${(idx % 3) + 1}`;

    return `
      <article class="product-card reveal ${delayClass}" data-id="${p.id}" style="${!inStock ? 'opacity: 0.72; background: #faf8f5;' : ''}">
        ${!inStock 
          ? `<span class="product-badge" style="background: #e0ded9; color: #696560;">Раскуплено</span>` 
          : (p.badge ? `<span class="product-badge">${p.badge}</span>` : "")
        }
        <div class="product-visual">
          ${p.image ? `<img src="${p.image}" alt="${p.name}" loading="lazy">` : p.icon}
        </div>
        <h3 class="product-title">${p.name}</h3>
        <p class="product-desc">${p.desc}</p>
        <div class="product-footer">
          <div class="product-price">
            <span class="price-val">${p.price} ₽</span>
            <span class="price-unit">${p.unit}</span>
          </div>
          <div class="product-actions">
            ${!inStock 
              ? `<button class="add-to-cart-btn" disabled style="background: #a3aba3; cursor: not-allowed;">Закончилось</button>`
              : `
                <button class="add-to-cart-btn" style="${qty > 0 ? 'display: none;' : ''}" onclick="addToCart('${p.id}')">
                  В корзину
                </button>
                <div class="qty-control ${qty > 0 ? 'active' : ''}">
                  <button class="qty-btn" onclick="updateQty('${p.id}', -1)">−</button>
                  <span class="qty-val">${qty}</span>
                  <button class="qty-btn" onclick="updateQty('${p.id}', 1)">+</button>
                </div>
              `
            }
          </div>
        </div>
      </article>
    `;
  }).join("");

  initScrollReveal();
}

// Управление корзиной
window.addToCart = function(productId) {
  state.cart[productId] = (state.cart[productId] || 0) + 1;
  updateCartUI();
  renderProducts();
};

window.updateQty = function(productId, delta) {
  const current = state.cart[productId] || 0;
  const next = current + delta;
  if (next <= 0) {
    delete state.cart[productId];
  } else {
    state.cart[productId] = next;
  }
  updateCartUI();
  renderProducts();
  if (cartModal.classList.contains("open")) {
    renderCartModalItems();
  }
};

function getCartStats() {
  let count = 0;
  let total = 0;
  for (const [id, qty] of Object.entries(state.cart)) {
    const product = liveProducts.find(p => p.id === id);
    if (product) {
      count += qty;
      total += product.price * qty;
    }
  }
  return { count, total };
}

// --------------------------------------------------------------------------
// Логика корзины и оформления заказа
// --------------------------------------------------------------------------

let isMainButtonBound = false;

function updateCartUI() {
  const { count, total } = getCartStats();
  
  if (cartBadge) {
    cartBadge.textContent = count;
  }
  
  if (stickyCartBar) {
    if (count > 0) {
      stickyCartBar.classList.add("visible");
      stickyCartItems.textContent = `${count} ${pluralize(count, ['товар', 'товара', 'товаров'])}`;
      stickyCartTotal.textContent = `${total} ₽`;
    } else {
      stickyCartBar.classList.remove("visible");
    }
  }

  // Telegram MainButton интеграция (если открыто внутри Telegram)
  if (tg?.initData && tg?.MainButton) {
    if (count > 0) {
      tg.MainButton.setText(`Оформить заказ • ~${total} ₽`);
      tg.MainButton.show();
      if (!isMainButtonBound) {
        tg.MainButton.onClick(openCartModal);
        isMainButtonBound = true;
      }
    } else {
      tg.MainButton.hide();
    }
  }
}

// Модальное окно корзины
function openCartModal() {
  const { count } = getCartStats();
  if (count === 0) return;
  renderCartModalItems();
  cartModal.classList.add("open");
}

function closeCartModal() {
  cartModal.classList.remove("open");
}

function renderCartModalItems() {
  const { count, total } = getCartStats();
  if (count === 0) {
    closeCartModal();
    return;
  }

  cartItemsList.innerHTML = Object.entries(state.cart).map(([id, qty]) => {
    const p = liveProducts.find(prod => prod.id === id);
    if (!p) return "";
    return `
      <div class="cart-item">
        <div>
          <div class="cart-item-name">${p.icon} ${p.name}</div>
          <div class="cart-item-price">${p.price} ₽ × ${qty} = <b>${p.price * qty} ₽</b></div>
        </div>
        <div class="qty-control active">
          <button class="qty-btn" onclick="updateQty('${p.id}', -1)">−</button>
          <span class="qty-val">${qty}</span>
          <button class="qty-btn" onclick="updateQty('${p.id}', 1)">+</button>
        </div>
      </div>
    `;
  }).join("");

  cartModalTotal.textContent = `${total} ₽`;
}

// Отправка формы заказа
if (checkoutForm) {
  checkoutForm.addEventListener("submit", async function(e) {
    e.preventDefault();
    const { count, total } = getCartStats();
    if (count === 0) return;

    const name = document.getElementById("clientName").value.trim();
    const phone = document.getElementById("clientPhone").value.trim();
    const address = document.getElementById("clientAddress").value.trim();
    const comment = document.getElementById("clientComment")?.value.trim() || "";

    const orderData = {
      client: { name, phone, address, comment },
      items: Object.entries(state.cart).map(([id, qty]) => {
        const p = liveProducts.find(prod => prod.id === id);
        return { id, name: p.name, price: p.price, qty, subtotal: p.price * qty };
      }),
      total,
      createdAt: new Date().toISOString()
    };

    const submitBtn = checkoutForm.querySelector(".submit-order-btn") || document.querySelector(".submit-order-btn");
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = "Отправка заказа...";
    }

    // 1. Формируем подробный отчет по заказу для Telegram
    const tgUser = tg?.initDataUnsafe?.user;
    const userMention = tgUser 
      ? `@${tgUser.username || 'нет_ника'} (${tgUser.first_name || ''}, ID: <code>${tgUser.id}</code>)` 
      : 'через браузер/сайт';

    const itemsFormatted = Object.entries(state.cart).map(([id, qty]) => {
      const p = liveProducts.find(prod => prod.id === id);
      return `• <b>${p.name}</b>: ${qty} шт. × ${p.price} ₽ = <b>${p.price * qty} ₽</b>`;
    }).join("\n");

    const messageHtml = 
`🔔 <b>НОВЫЙ ЗАКАЗ — ДЕЖКИНО!</b>

👤 <b>Покупатель:</b> ${name}
📞 <b>Телефон:</b> <a href="tel:${phone}">${phone}</a>
📍 <b>Адрес:</b> ${address}
${comment ? `💬 <b>Пожелания:</b> ${comment}\n` : ''}📱 <b>Клиент в TG:</b> ${userMention}

🛒 <b>Состав заказа:</b>
${itemsFormatted}

💰 <b>Итого к оплате:</b> <b>${total} ₽</b> (оплата по факту проверки)`;

    // 2. Прямая отправка в Telegram Bot API (работает мгновенно 24/7 с GitHub Pages!)
    try {
      await fetch("https://api.telegram.org/bot8977077034:AAF0N-kUmFkIn717Y4esrS6VEoBD2nKC2uY/sendMessage", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: "6374158037",
          text: messageHtml,
          parse_mode: "HTML"
        })
      });
    } catch (tgErr) {
      console.warn("Direct TG dispatch fallback:", tgErr);
    }

    // 3. Дублируем через tg.sendData, если Mini App открыт по кнопке клавиатуры
    try {
      if (tg && typeof tg.sendData === "function") {
        tg.sendData(JSON.stringify(orderData));
      }
    } catch (e) {}

    // 4. Локальный fallback (если запущен локальный Python сервер)
    try {
      await fetch("/api/order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(orderData)
      });
    } catch (err) {}

    // Сброс корзины и закрытие модалки
    state.cart = {};
    updateCartUI();
    renderProducts();
    closeCartModal();
    checkoutForm.reset();
    
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = "Подтвердить заказ";
    }

    showSuccessModal(name, total);
  });
}

function showSuccessModal(name, total) {
  const modal = document.getElementById("successModal");
  if (modal) {
    document.getElementById("successClientName").textContent = name;
    document.getElementById("successOrderTotal").textContent = `${total} ₽`;
    modal.classList.add("open");
  } else {
    alert(`🎉 Спасибо, ${name}!\nЗаказ на сумму ~${total} ₽ принят.`);
  }
}

function pluralize(n, forms) {
  n = Math.abs(n) % 100;
  const n1 = n % 10;
  if (n > 10 && n < 20) return forms[2];
  if (n1 > 1 && n1 < 5) return forms[1];
  if (n1 === 1) return forms[0];
  return forms[2];
}

// Плавная анимация появления при скролле (Scroll Reveal в стиле Patagonia)
function initScrollReveal() {
  const reveals = document.querySelectorAll(".reveal:not(.is-visible)");
  if (!reveals.length) return;

  if (!("IntersectionObserver" in window)) {
    reveals.forEach(el => el.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.08,
    rootMargin: "0px 0px -30px 0px"
  });

  reveals.forEach(el => observer.observe(el));
}

// Привязка кнопок открытия корзины
document.getElementById("headerCartBtn")?.addEventListener("click", openCartModal);
document.getElementById("stickyCartBar")?.addEventListener("click", openCartModal);
document.getElementById("modalCloseBtn")?.addEventListener("click", closeCartModal);

// Закрытие по клику на оверлей
cartModal?.addEventListener("click", (e) => {
  if (e.target === cartModal) closeCartModal();
});

// Первоначальный рендер
renderCategories();
renderProducts();
updateCartUI();
initScrollReveal();
fetchLiveProducts();
