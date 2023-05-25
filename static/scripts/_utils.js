const params = new Proxy(new URLSearchParams(window.location.search), {
  get: (searchParams, prop) => searchParams.get(prop),
});
function toggle_popup(id) {
    console.log("toggled " + id);
    document.getElementById(id).classList.toggle("revealed");
}

function toggle_focus_blur(id) {
    document.getElementById(id).classList.toggle("focus-blur");
}

function selectGameOption (selectedOption, option_type_class) {
  let elemGameOptionsContainer = document.querySelector("." + option_type_class);
  let elemGameOptions = document.querySelectorAll("." + option_type_class + " input");
  let multOption = elemGameOptionsContainer.classList.contains("mult");
  let selectCount = 1;

  if (selectedOption.classList.contains("disabled")) {
      return
  }

  console.log(option_type_class)
  // Deselects all
  for (let i = 0; i < elemGameOptions.length; i++) {
      let elemGameOption = elemGameOptions[i];
      if (elemGameOption.classList.contains("selected") && !multOption) {
          elemGameOption.classList.toggle("selected");

      }
  }

  console.log("selectCount: " + selectCount)

  // Selects one selected
  if (!selectedOption.classList.contains("selected") || multOption){
      selectedOption.classList.toggle("selected");
      document.getElementById(option_type_class).value = selectedOption.name;
  }

}

function redirect(path) {
    location.href = path;
}
