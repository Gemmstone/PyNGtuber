var elementsOpen = document.getElementsByClassName("talking_open");
var elementsClosed = document.getElementsByClassName("talking_closed");
var elementsScreaming = document.getElementsByClassName("talking_screaming");
// var imageWrapper = document.getElementById("image-wrapper");
var imageWrapper = document.querySelectorAll(".idle_animation");
var imageAddedWrapper = document.querySelectorAll(".added_animation");

while(true) {
  var status = Math.floor(Math.random() * 3);
  
  var opacityOpen = (status == 1) ? 1 : 0;
  var opacityClosed = (status <= 1) ? 1 : 0;
  var opacityScreaming = (status == 2) ? 1 : 0;
  
  // Apply CSS transitions for a smooth animation to text elements
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
              var animation = "floaty";
              var speed = "0.500";
              image.style.animation = animation + " " + speed + "s ease-in-out infinite";
          } else {
              var animation = "floaty";
              var speed = "6.000";
              image.style.animation = animation + " " + speed + "s ease-in-out infinite";
          }
      });
  }
  if(imageAddedWrapper.length > 0) {
      imageAddedWrapper.forEach(function(animation_div) {
          if (status == 1 || status == 2) {
              animation_div.style.animation = animation_div.attributes.animation_name_talking.value + " " + animation_div.attributes.animation_speed_talking.value + "s ease-in-out infinite";
          } else {
              animation_div.style.animation = animation_div.attributes.animation_name_idle.value + " " + animation_div.attributes.animation_speed_idle.value + "s ease-in-out infinite";
          }
      });
  }
  setTimeout(2000)
}
