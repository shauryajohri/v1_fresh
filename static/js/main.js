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

    // ── Product-card quantity control: "Add to cart" ⇄ − qty + ─────
    function cardWeight(control) {
        const card = control.closest(".product-card");
        const sel = card && card.querySelector(".weight-chip.is-selected");
        if (sel) return sel.dataset.label || "";
        const any = card && card.querySelector(".weight-chip");
        return any ? (any.dataset.label || "") : "";
    }
    function cardQty(productId, weight) {
        const cart = window.V1_CART || {};
        return cart[productId + "|" + weight] || 0;
    }
    function renderCardControl(control, qty) {
        const addBtn = control.querySelector(".btn-add-cart-full");
        const stepper = control.querySelector(".card-qty-stepper");
        const valEl = control.querySelector(".card-qty-value");
        if (!addBtn || !stepper) return;
        addBtn.hidden = qty > 0;
        stepper.hidden = qty <= 0;
        if (valEl) valEl.textContent = qty > 0 ? qty : 0;
    }
    async function setCardQty(control, newQty) {
        const productId = control.dataset.productId;
        const weight = cardWeight(control);
        try {
            const res = await fetch("/cart/update", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ product_id: parseInt(productId), weight_label: weight, quantity: newQty }),
            });
            const data = await res.json();
            if (!data.ok) return;
            window.V1_CART = window.V1_CART || {};
            const key = productId + "|" + weight;
            if (data.quantity > 0) window.V1_CART[key] = data.quantity;
            else delete window.V1_CART[key];
            renderCardControl(control, data.quantity);
            updateBadge(data.cart_count);
        } catch (e) { /* network error — ignore */ }
    }
    // Reflect existing cart quantities on load.
    document.querySelectorAll(".card-cart-control").forEach((control) => {
        renderCardControl(control, cardQty(control.dataset.productId, cardWeight(control)));
    });
    // Stepper +/- clicks.
    document.body.addEventListener("click", (e) => {
        const inc = e.target.closest("[data-action='card-inc']");
        const dec = e.target.closest("[data-action='card-dec']");
        if (!inc && !dec) return;
        const control = (inc || dec).closest(".card-cart-control");
        if (!control) return;
        const cur = cardQty(control.dataset.productId, cardWeight(control));
        setCardQty(control, inc ? cur + 1 : cur - 1);
    });

    // ── ADD button handler (works on all pages) ────────────────
    document.body.addEventListener("click", async (e) => {
        const btn = e.target.closest("[data-action='add']");
        if (!btn) return;

        // Product cards: switch to the quantity stepper instead of a one-shot add.
        const cardControl = btn.closest(".card-cart-control");
        if (cardControl) {
            const cur = cardQty(cardControl.dataset.productId, cardWeight(cardControl));
            setCardQty(cardControl, cur + 1);
            return;
        }

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

    // ── Wishlist (persisted in localStorage) ───────────────────────────
    function getWishlist() {
        try { return JSON.parse(localStorage.getItem("v1fresh_wishlist") || "[]"); }
        catch (e) { return []; }
    }
    function saveWishlist(ids) {
        try { localStorage.setItem("v1fresh_wishlist", JSON.stringify(ids)); } catch (e) {}
        const badge = document.getElementById("wishlistBadge");
        if (badge) {
            badge.textContent = ids.length;
            badge.style.display = ids.length ? "" : "none";
        }
    }
    // Restore heart state + badge on every page load.
    (function restoreWishlist() {
        const ids = getWishlist();
        document.querySelectorAll(".product-card[data-product-id]").forEach((card) => {
            if (ids.includes(card.dataset.productId)) {
                const heart = card.querySelector("[data-action='wishlist']");
                if (heart) heart.classList.add("is-active");
            }
        });
        saveWishlist(ids); // syncs the badge
    })();

    // ── Wishlist heart toggle + weight-chip selector ──
    document.body.addEventListener("click", (e) => {
        const wishlistBtn = e.target.closest("[data-action='wishlist']");
        if (wishlistBtn) {
            const card = wishlistBtn.closest(".product-card");
            const id = card ? card.dataset.productId : null;
            if (id) {
                let ids = getWishlist();
                if (ids.includes(id)) {
                    ids = ids.filter((x) => x !== id);
                    wishlistBtn.classList.remove("is-active");
                } else {
                    ids.push(id);
                    wishlistBtn.classList.add("is-active");
                }
                saveWishlist(ids);
            }
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
            // Re-sync the add/stepper control for the newly selected weight.
            const ctrl = card ? card.querySelector(".card-cart-control") : null;
            if (ctrl) renderCardControl(ctrl, cardQty(ctrl.dataset.productId, chip.dataset.label));
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
            const savingsEl = info.querySelector("[data-role='detail-savings']");
            if (savingsEl && !isNaN(baseMrp) && !isNaN(basePrice) && !isNaN(fraction)) {
                savingsEl.textContent = "You save ₹" + ((baseMrp - basePrice) * fraction).toFixed(2);
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

    // ── Live location: detect user's area via browser geolocation ──
    const locateBtn = document.getElementById("detectLocation");
    const locationLabel = document.getElementById("userLocation");

    // Restore a previously detected location for this browser
    try {
        const saved = localStorage.getItem("v1fresh_location");
        if (saved && locationLabel) locationLabel.textContent = saved;
    } catch (e) { /* storage unavailable — ignore */ }

    if (locateBtn && locationLabel) {
        const flash = (msg, revertTo, ms) => {
            locationLabel.textContent = msg;
            setTimeout(() => {
                if (locationLabel.textContent === msg) locationLabel.textContent = revertTo;
            }, ms || 3500);
        };

        locateBtn.addEventListener("click", () => {
            const original = locationLabel.textContent;

            if (!("geolocation" in navigator)) {
                flash("Location not supported", original);
                return;
            }
            // Browsers only allow geolocation on https:// or localhost.
            if (window.isSecureContext === false) {
                flash("Open on https/localhost", original, 4500);
                return;
            }

            locationLabel.textContent = "Detecting…";
            locateBtn.disabled = true;

            navigator.geolocation.getCurrentPosition(async (pos) => {
                const { latitude, longitude } = pos.coords;
                let label = "Your location";
                try {
                    const res = await fetch(
                        `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${latitude}&longitude=${longitude}&localityLanguage=en`
                    );
                    if (res.ok) {
                        const data = await res.json();
                        const area = data.locality || data.city || data.principalSubdivision || "";
                        const region = data.principalSubdivision || "";
                        if (area) label = (region && region !== area) ? `${area}, ${region}` : area;
                    }
                } catch (e) {
                    // We still have the coordinates even if the area lookup fails.
                    label = latitude.toFixed(2) + ", " + longitude.toFixed(2);
                }
                locationLabel.textContent = label;
                try { localStorage.setItem("v1fresh_location", label); } catch (e) {}
                locateBtn.disabled = false;
            }, (err) => {
                locateBtn.disabled = false;
                let msg = "Couldn't get location";
                if (err.code === err.PERMISSION_DENIED) msg = "Allow location access";
                else if (err.code === err.POSITION_UNAVAILABLE) msg = "Turn on device location";
                else if (err.code === err.TIMEOUT) msg = "Timed out — try again";
                flash(msg, original, 4500);
            }, { enableHighAccuracy: false, timeout: 15000, maximumAge: 300000 });
        });
    }

});