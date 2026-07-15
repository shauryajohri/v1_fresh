// v1fresh — main.js
document.addEventListener("DOMContentLoaded", () => {

// ── Toast notifications ─────────────────────────────────────
    function showToast(message, type, ms) {
        const container = document.getElementById("toastContainer");
        if (!container) return;
        const toast = document.createElement("div");
        toast.className = "toast" + (type ? " toast-" + type : "");
        toast.innerHTML = '<span class="toast-icon">🚚</span><span>' + message + "</span>";
        container.appendChild(toast);
        requestAnimationFrame(() => toast.classList.add("toast-visible"));
        setTimeout(() => {
            toast.classList.remove("toast-visible");
            setTimeout(() => toast.remove(), 300);
        }, ms || 4000);
    }

    // ── Free-delivery progress (cart hint + "you unlocked it" toast) ────
    // Tracks the delivery fee we last saw *this page load* so the toast only
    // fires the moment the cart actually crosses the threshold — not on
    // every page load where it's already free.
    let lastDeliveryFee = null;
    (function initFreeDeliveryTracking() {
        const summary = document.querySelector(".cart-summary[data-delivery-fee]");
        if (summary) lastDeliveryFee = parseFloat(summary.dataset.deliveryFee);
    })();
    function handleFreeDeliveryUpdate(subtotal, deliveryFee) {
        if (subtotal == null || deliveryFee == null) return;
        const hintEl = document.getElementById("freeDeliveryHint");
        const threshold = window.V1_FREE_DELIVERY_THRESHOLD || 0;
        if (hintEl) {
            const remaining = threshold - subtotal;
            if (remaining > 0) {
                hintEl.textContent = "Add ₹" + Math.ceil(remaining) + " more for free delivery";
                hintEl.hidden = false;
            } else {
                hintEl.hidden = true;
            }
        }
        const nowFree = deliveryFee <= 0 && subtotal > 0;
        if (lastDeliveryFee !== null && lastDeliveryFee > 0 && nowFree) {
            showToast("You've unlocked FREE delivery on this order!", "success");
        }
        lastDeliveryFee = deliveryFee;
    }

// ── Draggable floating buttons (WhatsApp / Call) ────────────
    function makeDraggable(el, storageKey) {
        if (!el) return;

        // Restore saved position
        const saved = JSON.parse(localStorage.getItem(storageKey) || "null");
        if (saved) {
            el.style.left = saved.left + "px";
            el.style.top = saved.top + "px";
            el.style.right = "auto";
            el.style.bottom = "auto";
        }

        let dragging = false;
        let moved = false;
        let startX, startY, startLeft, startTop;

        const onPointerDown = (e) => {
            dragging = true;
            moved = false;
            const rect = el.getBoundingClientRect();
            startX = e.clientX;
            startY = e.clientY;
            startLeft = rect.left;
            startTop = rect.top;
            el.style.left = startLeft + "px";
            el.style.top = startTop + "px";
            el.style.right = "auto";
            el.style.bottom = "auto";
            el.setPointerCapture(e.pointerId);
        };

        const onPointerMove = (e) => {
            if (!dragging) return;
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            if (Math.abs(dx) > 4 || Math.abs(dy) > 4) moved = true;
            if (!moved) return;

            let newLeft = startLeft + dx;
            let newTop = startTop + dy;

            // Keep within viewport bounds
            const maxLeft = window.innerWidth - el.offsetWidth;
            const maxTop = window.innerHeight - el.offsetHeight;
            newLeft = Math.min(Math.max(0, newLeft), maxLeft);
            newTop = Math.min(Math.max(0, newTop), maxTop);

            el.style.left = newLeft + "px";
            el.style.top = newTop + "px";
        };

        const onPointerUp = (e) => {
            if (!dragging) return;
            dragging = false;
            el.releasePointerCapture(e.pointerId);

            if (moved) {
                // Prevent the click/navigation that follows a drag
                const suppressClick = (ev) => {
                    ev.preventDefault();
                    ev.stopPropagation();
                    el.removeEventListener("click", suppressClick, true);
                };
                el.addEventListener("click", suppressClick, true);

                const rect = el.getBoundingClientRect();
                localStorage.setItem(storageKey, JSON.stringify({ left: rect.left, top: rect.top }));
            }
        };

        el.addEventListener("pointerdown", onPointerDown);
        el.addEventListener("pointermove", onPointerMove);
        el.addEventListener("pointerup", onPointerUp);
        el.addEventListener("pointercancel", onPointerUp);
    }

    makeDraggable(document.querySelector(".float-whatsapp"), "v1fresh_whatsapp_pos");

// ── Mobile nav toggle ──────────────────────────────────────
    const toggle = document.getElementById("mobileToggle");
    const navbarInner = document.querySelector(".navbar-inner");
    if (toggle && navbarInner) {
        toggle.addEventListener("click", () => {
            navbarInner.classList.toggle("nav-open");
        });
    }

    // ── User account dropdown ──────────────────────────────────
    const userBtn = document.getElementById("navUserBtn");
    const userMenu = document.getElementById("navUserMenu");
    if (userBtn && userMenu) {
        userBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            const willOpen = userMenu.hidden;
            userMenu.hidden = !willOpen;
            userBtn.setAttribute("aria-expanded", String(willOpen));
        });
        document.addEventListener("click", (e) => {
            if (!userMenu.hidden && !userMenu.contains(e.target) && e.target !== userBtn) {
                userMenu.hidden = true;
                userBtn.setAttribute("aria-expanded", "false");
            }
        });
    }

    // ── Product cards: click anywhere to open detail page ──────
    document.body.addEventListener("click", (e) => {
        const card = e.target.closest(".product-card[data-href]");
        if (!card) return;
        // Don't hijack clicks on interactive elements inside the card —
        // links, buttons, and the weight-chip selector handle themselves.
        if (e.target.closest("a, button, .weight-chip")) return;
        window.location.href = card.dataset.href;
    });

    // ── Product carousels: looping next/prev arrows (no free scroll) ──
    document.querySelectorAll(".carousel:not(.carousel-cylinder)").forEach((carousel) => {
        const track = carousel.querySelector(".carousel-track");
        const prev = carousel.querySelector(".carousel-prev");
        const next = carousel.querySelector(".carousel-next");
        if (!track) return;
        const step = () => {
            const card = track.querySelector(".product-card, .product-grid > *");
            if (!card) return track.clientWidth * 0.9;
            const gap = parseFloat(getComputedStyle(track).columnGap || getComputedStyle(track).gap || "0") || 0;
            return card.getBoundingClientRect().width + gap;
        };
        const maxScroll = () => track.scrollWidth - track.clientWidth;
        if (next) next.addEventListener("click", () => {
            if (track.scrollLeft >= maxScroll() - 4) {
                track.scrollTo({ left: 0, behavior: "smooth" });        // loop back to the first
            } else {
                track.scrollBy({ left: step(), behavior: "smooth" });
            }
        });
        if (prev) prev.addEventListener("click", () => {
            if (track.scrollLeft <= 4) {
                track.scrollTo({ left: maxScroll(), behavior: "smooth" }); // loop to the last
            } else {
                track.scrollBy({ left: -step(), behavior: "smooth" });
            }
        });
    });

    // ── "Cylinder" carousel (Seasonal Picks): no free drag/swipe scroll —
    // arrows rotate the cards endlessly in both directions. Implemented by
    // sliding the track exactly one card-width, then — once the slide has
    // finished — silently moving the edge card to the opposite end and
    // resetting the transform to 0 (no transition), so the same set of
    // cards keeps circling around forever like a rotating drum.
    document.querySelectorAll(".carousel-cylinder").forEach((carousel) => {
        const track = carousel.querySelector(".carousel-track");
        const prev = carousel.querySelector(".carousel-prev");
        const next = carousel.querySelector(".carousel-next");
        if (!track) return;

        const cards = () => Array.from(track.children).filter((el) => el.nodeType === 1 && !el.classList.contains("empty-note"));
        if (cards().length < 2) return; // nothing to rotate

        let isAnimating = false;

        function stepWidth() {
            const first = cards()[0];
            const rect = first.getBoundingClientRect();
            const gap = parseFloat(getComputedStyle(track).columnGap || getComputedStyle(track).gap || "20") || 20;
            return rect.width + gap;
        }

        // `transitionend` isn't 100% guaranteed to fire — a transition can get
        // silently interrupted (e.g. hovering a card triggers its own
        // hover-transform layout recalc mid-slide, or the tab is backgrounded
        // for a moment). If that ever happens, `isAnimating` would stay stuck
        // `true` forever and the arrows would go dead permanently. A fallback
        // timer guarantees the rotation always completes and the lock always
        // releases, no matter what the browser does with the real event.
        const TRANSITION_MS = 350;
        const SAFETY_MS = TRANSITION_MS + 150;

        function runOnce(track, fn) {
            let done = false;
            return () => {
                if (done) return;
                done = true;
                fn();
            };
        }

        function goNext() {
            if (isAnimating) return;
            isAnimating = true;
            const dist = stepWidth();
            track.style.transition = "transform " + TRANSITION_MS + "ms ease";
            track.style.transform = "translateX(-" + dist + "px)";

            const finish = runOnce(track, () => {
                track.removeEventListener("transitionend", onEnd);
                clearTimeout(safety);
                track.style.transition = "none";
                track.appendChild(cards()[0]); // first card rotates to the end
                track.style.transform = "translateX(0)";
                // Force a reflow so the "no transition" reset applies before
                // the next click re-enables the transition.
                void track.offsetHeight;
                isAnimating = false;
            });
            const onEnd = (e) => { if (e.target === track && e.propertyName === "transform") finish(); };
            track.addEventListener("transitionend", onEnd);
            const safety = setTimeout(finish, SAFETY_MS);
        }

        function goPrev() {
            if (isAnimating) return;
            isAnimating = true;
            const dist = stepWidth();

            // Move the last card to the front first, instantly, pre-offset
            // by one card-width to the left so nothing visibly jumps —
            // then animate back to translateX(0) to reveal it sliding in.
            track.style.transition = "none";
            const last = cards()[cards().length - 1];
            track.insertBefore(last, track.firstChild);
            track.style.transform = "translateX(-" + dist + "px)";
            void track.offsetHeight;

            requestAnimationFrame(() => {
                track.style.transition = "transform " + TRANSITION_MS + "ms ease";
                track.style.transform = "translateX(0)";
                const finish = runOnce(track, () => {
                    track.removeEventListener("transitionend", onEnd);
                    clearTimeout(safety);
                    isAnimating = false;
                });
                const onEnd = (e) => { if (e.target === track && e.propertyName === "transform") finish(); };
                track.addEventListener("transitionend", onEnd);
                const safety = setTimeout(finish, SAFETY_MS);
            });
        }

        if (next) next.addEventListener("click", goNext);
        if (prev) prev.addEventListener("click", goPrev);

        // Keep the rotation math correct if the viewport is resized
        // (card width changes at the 900px breakpoint).
        window.addEventListener("resize", () => {
            if (!isAnimating) {
                track.style.transition = "none";
                track.style.transform = "translateX(0)";
            }
        });
    });
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
            handleFreeDeliveryUpdate(data.subtotal, data.delivery_fee);
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
                handleFreeDeliveryUpdate(data.subtotal, data.delivery_fee);
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

    // ── Login-required popup (checkout / wishlist while signed out) ────
    function showLoginPrompt(message, nextPath) {
        const modal = document.getElementById("loginPromptModal");
        if (!modal) {
            window.location.href = "/login" + (nextPath ? "?next=" + encodeURIComponent(nextPath) : "");
            return;
        }
        const msgEl = document.getElementById("loginPromptMsg");
        if (msgEl && message) msgEl.textContent = message;
        const btn = document.getElementById("loginPromptBtn");
        if (btn) btn.href = "/login?next=" + encodeURIComponent(nextPath || window.location.pathname);
        modal.hidden = false;
        document.body.classList.add("modal-open");
    }
    function hideLoginPrompt() {
        const modal = document.getElementById("loginPromptModal");
        if (modal) modal.hidden = true;
        document.body.classList.remove("modal-open");
    }
    document.body.addEventListener("click", (e) => {
        if (e.target.closest("[data-action='close-login-modal']")) { hideLoginPrompt(); return; }
        if (e.target.id === "loginPromptModal") { hideLoginPrompt(); return; }
    });
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") hideLoginPrompt();
    });

    // "Proceed to Checkout" while signed out → popup instead of navigating.
    document.body.addEventListener("click", (e) => {
        const checkoutLink = e.target.closest("[data-action='checkout-link']");
        if (checkoutLink && !window.V1_LOGGED_IN) {
            e.preventDefault();
            showLoginPrompt("Please sign in to proceed to checkout.", "/checkout");
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
            badge.style.display = ids.length ? "inline-flex" : "none";
        }
        // Also persist to the signed-in user's account.
        if (window.V1_LOGGED_IN) {
            fetch("/wishlist/save", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ids: ids }) }).catch(function () {});
        }
    }
    // Merge the account wishlist (loaded at login) into this browser's list.
    if (window.V1_WISHLIST_SAVED && window.V1_WISHLIST_SAVED.length) {
        try {
            const local = getWishlist();
            const merged = Array.from(new Set(local.concat(window.V1_WISHLIST_SAVED.map(String))));
            localStorage.setItem("v1fresh_wishlist", JSON.stringify(merged));
        } catch (e) {}
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
            if (!window.V1_LOGGED_IN) {
                showLoginPrompt("Please sign in to save items to your wishlist.", window.location.pathname);
                return;
            }
            const card = wishlistBtn.closest(".product-card");
            const id = wishlistBtn.dataset.productId || (card ? card.dataset.productId : null);
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
        handleFreeDeliveryUpdate(data.subtotal, data.delivery_fee);
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