// v1fresh — main.js
document.addEventListener("DOMContentLoaded", () => {

// ── Mobile nav toggle ──────────────────────────────────────
    const toggle = document.getElementById("mobileToggle");
    const navbarInner = document.querySelector(".navbar-inner");
    if (toggle && navbarInner) {
        toggle.addEventListener("click", () => {
            navbarInner.classList.toggle("nav-open");
        });
    }
    // ── Hide topbar on scroll ───────────────────────────────────
const siteHeader = document.getElementById("siteHeader");
const topbarEl = siteHeader ? siteHeader.querySelector(".topbar") : null;
if (topbarEl) {
    const HIDE_THRESHOLD = 80;  // scroll past this to hide
    const SHOW_THRESHOLD = 20;  // scroll back above this to show again
    let isHidden = false;
    let ticking = false;

    function handleTopbarScroll() {
        const y = window.scrollY;
        if (!isHidden && y > HIDE_THRESHOLD) {
            topbarEl.classList.add("is-hidden");
            isHidden = true;
        } else if (isHidden && y < SHOW_THRESHOLD) {
            topbarEl.classList.remove("is-hidden");
            isHidden = false;
        }
        ticking = false;
    }

    window.addEventListener("scroll", () => {
        if (!ticking) {
            requestAnimationFrame(handleTopbarScroll);
            ticking = true;
        }
    }, { passive: true });

    handleTopbarScroll();
}
    // ── Hero banner slider (auto-rotates + clickable dots) ─────
    const heroSlider = document.getElementById("heroSlider");
    if (heroSlider) {
        const slides = heroSlider.querySelectorAll(".hero-slide");
        const dots = heroSlider.querySelectorAll(".hero-dot");
        let currentIndex = 0;
        let autoRotateTimer = null;
        const SLIDE_DURATION_MS = 4000;

        function goToSlide(index) {
            slides[currentIndex].classList.remove("is-active");
            dots[currentIndex].classList.remove("is-active");
            currentIndex = index;
            slides[currentIndex].classList.add("is-active");
            dots[currentIndex].classList.add("is-active");
        }

        function nextSlide() {
            const next = (currentIndex + 1) % slides.length;
            goToSlide(next);
        }

        function startAutoRotate() {
            stopAutoRotate();
            autoRotateTimer = setInterval(nextSlide, SLIDE_DURATION_MS);
        }

        function stopAutoRotate() {
            if (autoRotateTimer) clearInterval(autoRotateTimer);
        }

        dots.forEach((dot, i) => {
            dot.addEventListener("click", () => {
                goToSlide(i);
                startAutoRotate(); // reset the timer after a manual click
            });
        });

        if (slides.length > 1) {
            startAutoRotate();
        }
    }

    // ── Cart badge updater ─────────────────────────────────────
    function updateBadge(count) {
        const badge = document.getElementById("cartBadge");
        if (badge) badge.textContent = count;
    }

    // ── ADD button handler (works on all pages) ────────────────
    document.body.addEventListener("click", async (e) => {
        const btn = e.target.closest("[data-action='add']");
        if (!btn) return;

        const productId = btn.dataset.productId;
        if (!productId) return;

        btn.disabled = true;
        btn.textContent = "Adding...";

        // Product detail page: a plain quantity selector
        const qtySelector = btn.closest(".qty-cart-row")?.querySelector(".qty-value");
        const quantity = qtySelector ? (parseInt(qtySelector.textContent, 10) || 1) : 1;
// Product card: whichever weight chip is currently selected
        const selectedChip = btn.closest(".product-card")?.querySelector(".weight-chip.is-selected");
        // Product detail page: weight is tracked on the button itself, kept in
        // sync by the detail-chip click handler below
        const weightLabel = selectedChip ? selectedChip.dataset.label : btn.dataset.weightLabel || null;

        try {
            const res = await fetch("/cart/add", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    product_id: parseInt(productId),
                    quantity,
                    weight_label: weightLabel,
                }),
            });

            const data = await res.json();

            if (data.ok) {
                updateBadge(data.cart_count);
                btn.textContent = "✓ Added";
                btn.style.background = "var(--green-700)";
                setTimeout(() => {
                    btn.textContent = "ADD";
                    btn.style.background = "";
                    btn.disabled = false;
                }, 1200);
            } else {
                btn.textContent = data.error || "Error";
                setTimeout(() => {
                    btn.textContent = "ADD";
                    btn.disabled = false;
                }, 1500);
            }
        } catch (err) {
            btn.textContent = "Error";
            setTimeout(() => {
                btn.textContent = "ADD";
                btn.disabled = false;
            }, 1500);
        }
    });

    // ── Wishlist heart + weight-chip selector (decorative, front-end only) ──
    document.body.addEventListener("click", (e) => {
        const wishlistBtn = e.target.closest("[data-action='wishlist']");
        if (wishlistBtn) {
            wishlistBtn.classList.toggle("is-active");
            return;
        }

        const chip = e.target.closest("[data-action='chip']");
        if (chip) {
            const row = chip.closest(".weight-chip-row");
            row.querySelectorAll(".weight-chip").forEach((c) => c.classList.remove("is-selected"));
            chip.classList.add("is-selected");

            // Recompute the displayed price for this card from base price × fraction
            const card = chip.closest(".product-card");
            const priceEl = card ? card.querySelector(".price") : null;
            const basePrice = parseFloat(row.dataset.basePrice);
            const fraction = parseFloat(chip.dataset.fraction);
            if (priceEl && !isNaN(basePrice) && !isNaN(fraction)) {
                priceEl.textContent = "₹" + Math.round(basePrice * fraction);
            }
        }

        // Product detail page weight chips
        const detailChip = e.target.closest("[data-action='detail-chip']");
        if (detailChip) {
            const row = detailChip.closest(".detail-weight-chip-row");
            row.querySelectorAll(".detail-weight-chip").forEach((c) => c.classList.remove("is-selected"));
            detailChip.classList.add("is-selected");

            const fraction = parseFloat(detailChip.dataset.fraction);
            const label = detailChip.dataset.label;
            const basePrice = parseFloat(row.dataset.basePrice);
            const baseMrp = parseFloat(row.dataset.baseMrp);

            const info = row.closest(".product-detail-info");
            const priceEl = info.querySelector("[data-role='detail-price']");
            const mrpEl = info.querySelector("[data-role='detail-mrp']");
            const perUnitEl = info.querySelector("[data-role='detail-per-unit']");
            const addBtn = info.querySelector(".btn-add-cart-large");

            if (priceEl && !isNaN(basePrice) && !isNaN(fraction)) {
                priceEl.textContent = "₹" + Math.round(basePrice * fraction);
            }
            if (mrpEl && !isNaN(baseMrp) && !isNaN(fraction)) {
                mrpEl.textContent = "₹" + Math.round(baseMrp * fraction);
            }
            if (perUnitEl) {
                perUnitEl.textContent = "/ " + label;
            }
            if (addBtn) {
                addBtn.dataset.weightLabel = label;
            }

            updateDetailTotal(info);
        }
    });

    // ── Product detail page: keep "Total: ₹.." in sync with qty × unit price ──
    function updateDetailTotal(info) {
        if (!info) return;
        const totalEl = info.querySelector("[data-role='detail-total']");
        const priceEl = info.querySelector("[data-role='detail-price']");
        const qtyEl = info.querySelector(".qty-value");
        if (!totalEl || !priceEl || !qtyEl) return;

        const unitPrice = parseFloat(priceEl.textContent.replace(/[^\d.]/g, ""));
        const qty = parseInt(qtyEl.textContent, 10) || 1;
        if (isNaN(unitPrice)) return;

        totalEl.textContent = "Total: ₹" + (unitPrice * qty).toFixed(2);
    }

    // ── Quantity +/- and remove handlers (cart page + product detail) ──
    document.body.addEventListener("click", async (e) => {
        const qtyBtn = e.target.closest(".qty-btn");
        const removeBtn = e.target.closest("[data-action='remove']");

        if (qtyBtn) {
            const selector = qtyBtn.closest(".qty-selector");
            if (!selector) return;
            const valueEl = selector.querySelector(".qty-value");
            let qty = parseInt(valueEl.textContent, 10) || 1;
            qty = qtyBtn.dataset.action === "increase" ? qty + 1 : qty - 1;
            if (qty < 1) qty = 1;

            const cartItem = selector.closest(".cart-item");
            if (cartItem) {
                // Already in the cart (cart.html) — persist the change
                await updateCartQuantity(cartItem.dataset.productId, cartItem.dataset.weightLabel, qty, cartItem, valueEl);
            } else {
                // Not in the cart yet (product detail page) — just adjust the local selector
                valueEl.textContent = qty;
                updateDetailTotal(selector.closest(".product-detail-info"));
            }
            return;
        }

        if (removeBtn) {
            const cartItem = removeBtn.closest(".cart-item");
            if (!cartItem) return;
            await removeCartItem(cartItem.dataset.productId, cartItem.dataset.weightLabel, cartItem);
        }
    });

    async function updateCartQuantity(productId, weightLabel, quantity, cartItemEl, valueEl) {
        try {
            const res = await fetch("/cart/update", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ product_id: parseInt(productId), weight_label: weightLabel, quantity }),
            });
            const data = await res.json();
            if (!data.ok) return;

            valueEl.textContent = data.quantity;
            const lineTotalEl = cartItemEl.querySelector(".cart-item-total");
            if (lineTotalEl && data.line_total !== null) {
                lineTotalEl.textContent = "₹" + Math.round(data.line_total);
            }

            updateBadge(data.cart_count);
            refreshCartSummary(data);
        } catch (err) {
            console.error(err);
        }
    }

    async function removeCartItem(productId, weightLabel, cartItemEl) {
        try {
            const res = await fetch("/cart/remove", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ product_id: parseInt(productId), weight_label: weightLabel }),
            });
            const data = await res.json();
            if (!data.ok) return;

            cartItemEl.remove();
            updateBadge(data.cart_count);
            refreshCartSummary(data);

            const list = document.getElementById("cartItemsList");
            if (list && list.children.length === 0) location.reload(); // shows the "empty cart" state
        } catch (err) {
            console.error(err);
        }
    }

    function refreshCartSummary(data) {
        const subtotalEl = document.getElementById("cartSubtotal");
        const deliveryEl = document.getElementById("cartDeliveryFee");
        const totalEl = document.getElementById("cartTotal");
        if (subtotalEl) subtotalEl.textContent = "₹" + Math.round(data.subtotal);
        if (deliveryEl) deliveryEl.textContent = data.delivery_fee > 0 ? "₹" + Math.round(data.delivery_fee) : "FREE";
        if (totalEl) totalEl.textContent = "₹" + Math.round(data.total);
    }

});