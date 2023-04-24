let create_user_card = function (username, pfp_src, level, admin) {
    // List of player cards in this
    let div_player_container = document.querySelector(".player-container");

    // Create player elem

    // Player card container
    let div_player_card_container = document.createElement("div");
    div_player_card_container.className = "player-card-container";
    div_player_card_container.id = username;
    div_player_container.appendChild(div_player_card_container);

    ////// Children creation
    //// Player card
    let div_player_card = document.createElement("div");
    div_player_card.className = "player-card";
    div_player_card_container.appendChild(div_player_card);

    // Left side of card
    let div_left_side = document.createElement("div");
    div_left_side.className = "left side";
    div_player_card.append(div_left_side)
    let img_pfp = document.createElement("img");
    img_pfp.src = pfp_src;
    img_pfp.className = "player-picture";
    img_pfp.alt = username + " pfp";
    div_left_side.appendChild(img_pfp);
    let div_player_name = document.createElement("div");
    div_player_name.className = "player-name";
    div_player_name.innerText = username;
    div_left_side.appendChild(div_player_name);


    // Right side of card
    let div_right_side = document.createElement("div");
    div_right_side.className = "right side";
    div_player_card.appendChild(div_right_side);
    let div_player_level = document.createElement("div");
    div_player_level.className = "player-level";
    div_player_level.innerText = level;
    div_right_side.appendChild(div_player_level);

    // Player role icon
    let icon_role = document.createElement("i");
    if (admin) {
        icon_role.className = "bx bxs-user-badge player-role"
    } else {
        icon_role.className = "bx bxs-user-rectangle player-role"
    }
    div_player_card_container.appendChild(icon_role);


}

let remove_player_card = function (username) {
    let player_card = document.getElementById(username);
    let player_container = document.querySelector("#start-game > div > div.lobby > div");

    player_container.removeChild(player_card);
}


let update_player_count = function () {
    let header = document.getElementById("player-count-header");
    header.innerText = "Lobby (" + playerCount + " players)";
}

window.getCookie = function(name) {
  let match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  if (match) return match[2];
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
