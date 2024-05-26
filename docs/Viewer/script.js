var elementsOpen = document.getElementsByClassName("talking_open");
var elementsClosed = document.getElementsByClassName("talking_closed");
var elementsScreaming = document.getElementsByClassName("talking_screaming");
var imageWrapper = document.querySelectorAll(".idle_animation");
var imageAddedWrapper = document.querySelectorAll(".added_animation");

function resolveAfter2Seconds() {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve('resolved');
    }, 2000);
  });
}

async function asyncCall() {
  while(true) {
    
    var status = await Math.floor(Math.random() * 2);

    var opacityOpen = (status == 1) ? 1 : 0;
    var opacityClosed = (status <= 0) ? 1 : 0;
    var opacityScreaming = (status == 2) ? 1 : 0;

    for (var i = 0; i < elementsOpen.length; i++) {
        elementsOpen[i].style.transition = "opacity 0.3s";
        elementsOpen[i].style.opacity = opacityOpen;
    }

    for (var i = 0; i < elementsClosed.length; i++) {
        elementsClosed[i].style.transition = "opacity 0.3s";
        elementsClosed[i].style.opacity = opacityClosed;
    }

    for (var i = 0; i < elementsScreaming.length; i++) {
        elementsScreaming[i].style.transition = "opacity 0.3s";
        elementsScreaming[i].style.opacity = opacityScreaming;
    }

    if(imageWrapper.length > 0) {
        imageWrapper.forEach(function(image) {
            if (status == 1 || status == 2) {
                var speed = 0.500;
           } else {
               var speed = 6.000;
           }
           var animation = "floaty";
           var direction = "normal";
           image.style.animation = `${animation} ${speed}s ease-in-out infinite`;
           image.style.animationDirection = direction;
        });
    }
    if(imageAddedWrapper.length > 0) {
        imageAddedWrapper.forEach(function(animation_div) {
            if (status == 1 || status == 2) {
                var animation = animation_div.attributes.animation_name_talking.value;
                var speed = animation_div.attributes.animation_speed_talking.value;
                var direction = animation_div.attributes.animation_direction_talking.value;
            } else {
                var animation = animation_div.attributes.animation_name_idle.value;
                var speed = animation_div.attributes.animation_speed_idle.value;
                var direction = animation_div.attributes.animation_direction_idle.value;
            }
            animation_div.style.animation = `${animation} ${speed}s ease-in-out infinite`;
            animation_div.style.animationDirection = direction;
        });
    }
    
    await resolveAfter2Seconds();
  }
}

async function cursorPosition(X, Y){
    var cursor_divs = document.querySelectorAll(".cursor_div");
    if(cursor_divs.length > 0) {
        cursor_divs.forEach(function(cursor_div) {
            if(cursor_div.attributes.track_mouse_x.value == 1){
                if(cursor_div.attributes.invert_mouse_x.value == 1){
                    cursor_div.style.left = `calc(50% + ${X * cursor_div.attributes.cursorScaleX.value}px)`;
                } else {
                    cursor_div.style.left = `calc(50% + ${X * cursor_div.attributes.cursorScaleX.value * -1}px)`;
                }
            }
            if(cursor_div.attributes.track_mouse_y.value == 1){
                if(cursor_div.attributes.invert_mouse_y.value == 1){
                    cursor_div.style.top = `calc(50% - ${Y * (cursor_div.attributes.cursorScaleY.value * 2) * -1}px)`;
                } else {
                    cursor_div.style.top = `calc(50% - ${Y * (cursor_div.attributes.cursorScaleY.value * 2)}px)`;
                }
            }
        });
    }
}

function preventDefaultDrag(event) {
  event.preventDefault();
}

document.onmousemove = (event) => {
  var x = event.clientX * 2;
  var y = event.clientY * -2;
  document.getElementById("resultFrame").contentWindow.cursorPosition(x, y);
}

document.addEventListener("dragstart", preventDefaultDrag);

asyncCall();
