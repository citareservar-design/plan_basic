const btn = document.getElementById("themeToggle");
if (localStorage.theme === "dark" || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
  document.documentElement.classList.add("dark");
  btn.textContent = "☀️";
} else {
  document.documentElement.classList.remove("dark");
  btn.textContent = "🌙";
}
btn.addEventListener("click", () => {
  document.documentElement.classList.toggle("dark");
  if (document.documentElement.classList.contains("dark")) {
    localStorage.theme = "dark";
    btn.textContent = "☀️";
  } else {
    localStorage.theme = "light";
    btn.textContent = "🌙";
  }
});

