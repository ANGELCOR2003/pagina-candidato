// --- Menú hamburguesa con overlay ---
const burgerBtn = document.getElementById("burgerBtn");
const overlay = document.getElementById("overlay");
const overlayClose = document.getElementById("overlayClose");

function openMenu() {
  overlay?.classList.add("is-open");
  overlay?.setAttribute("aria-hidden", "false");
  burgerBtn?.setAttribute("aria-expanded", "true");
  document.body.style.overflow = "hidden";
}

function closeMenu() {
  overlay?.classList.remove("is-open");
  overlay?.setAttribute("aria-hidden", "true");
  burgerBtn?.setAttribute("aria-expanded", "false");
  document.body.style.overflow = "";
}

burgerBtn?.addEventListener("click", openMenu);
overlayClose?.addEventListener("click", closeMenu);

overlay?.addEventListener("click", (e) => {
  if (e.target === overlay) closeMenu();
});

// Cierra al navegar
document.querySelectorAll(".overlay-link").forEach((a) => {
  a.addEventListener("click", closeMenu);
});


// --- Carrusel simple (testimonios) ---
// Requiere:
// 1) Un contenedor con data-carousel
// 2) Dentro, un track con data-track (el que scrollea)
// 3) Botones con data-prev y data-next (opcionales)
document.querySelectorAll("[data-carousel]").forEach((carousel) => {
  const track = carousel.querySelector("[data-track]");
  const btnPrev = carousel.querySelector("[data-prev]");
  const btnNext = carousel.querySelector("[data-next]");

  if (!track) return;

  // Cuánto avanza por click: 90% del ancho visible o mínimo 280px
  const scrollAmount = () => Math.max(280, track.clientWidth * 0.9);

  btnNext?.addEventListener("click", () => {
    track.scrollBy({ left: scrollAmount(), behavior: "smooth" });
  });

  btnPrev?.addEventListener("click", () => {
    track.scrollBy({ left: -scrollAmount(), behavior: "smooth" });
  });

  // Drag con mouse (PC)
  let down = false;
  let startX = 0;
  let startScroll = 0;

  track.style.cursor = "grab";

  track.addEventListener("mousedown", (e) => {
    down = true;
    startX = e.pageX;
    startScroll = track.scrollLeft;
    track.style.cursor = "grabbing";
  });

  window.addEventListener("mouseup", () => {
    down = false;
    if (track) track.style.cursor = "grab";
  });

  window.addEventListener("mousemove", (e) => {
    if (!down) return;
    const dx = e.pageX - startX;
    track.scrollLeft = startScroll - dx;
  });
});

console.log("main.js cargó ✅");