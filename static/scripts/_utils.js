const params = new Proxy(new URLSearchParams(window.location.search), {
  get: (searchParams, prop) => searchParams.get(prop),
});
function toggle_popup(id) {
      document.getElementById(id).classList.toggle("revealed")
}