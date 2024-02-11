// Get the image container and the first image
const imageContainer = document.getElementById("image-wrapper");
const moveContainer = document.getElementById("move-wrapper");
const container = document.getElementById("container");

const leftButtons = [4,6,8,10,12,13,14,15];
const rightButtons = [0,1,2,3,5,7,9,11];

// Variables to track the mouse position and dragging state
let isDragging = false;
let initialMouseX;
let initialMouseY;
let initialImageX;
let initialImageY;

// Variables to store the current offset due to mouse movement
let mouseMovementX = 0;
let mouseMovementY = 0;

async function pool(){
    while(true){

        // Wheel / stick control

        var controllerWheels = document.querySelectorAll(".controller_wheel");
        if(controllerWheels.length > 0) {
            controllerWheels.forEach(function(controllerWheel) {

                let rawx = navigator.getGamepads()[controllerWheel.attributes.player.value].axes[0]
                let x = 0
                if(rawx > controllerWheel.attributes.deadzone.value)
                    x = rawx-controllerWheel.attributes.deadzone.value/(1-controllerWheel.attributes.deadzone.value)
                else if(rawx < -controllerWheel.attributes.deadzone.value)
                    x = rawx-controllerWheel.attributes.player.value/(1-controllerWheel.attributes.deadzone.value)
                let rotation = x * controllerWheel.attributes.deg.value;

                var currentTransform = controllerWheel.style.transform;
                var currentRotate = 0;
                if(currentTransform && currentTransform.includes("rotate")) {
                    var rotateIndex = currentTransform.indexOf("rotate");
                    var endIndex = currentTransform.indexOf("deg", rotateIndex);
                    currentRotate = parseFloat(currentTransform.substring(rotateIndex + 7, endIndex));
                }
                controllerWheel.style.transform = currentTransform.replace(`rotate(${currentRotate}deg)`, `rotate(${rotation}deg)`);
            });
        }

        // Button control
        var controllerButtons = document.querySelectorAll(".controller_buttons");
        if(controllerButtons.length > 0) {
            controllerButtons.forEach(function(controllerButton) {
                let buttons = navigator.getGamepads()[controllerButton.attributes.player.value].buttons
                let left = false
                let right = false

                for(let i = 0; i < buttons.length; i++){
                    if(buttons[i].pressed){
                        if(!left && leftButtons.indexOf(i) !== -1){
                            left = true
                        }else if(!right && rightButtons.indexOf(i) !== -1){
                            right = true
                        }
                    }
                }

                switch(true){
                    case left && right:
                        if (controllerButton.attributes.mode.value == "display") {
                            if (controllerButton.attributes.buttons.value == 3){
                                controllerButton.style.display = "block";
                            } else {
                                controllerButton.style.display = "none";
                            }
                        } else {
                            controllerButton.style.left = `calc(50% + ${controllerButton.attributes.posBothX.value}px)`;
                            controllerButton.style.top = `calc(50% + ${controllerButton.attributes.posBothY.value}px)`;
                            controllerButton.style.transform = `rotate(${controllerButton.attributes.rotationBoth.value}deg)`;
                        }
                        break;
                    case left:
                        if (controllerButton.attributes.mode.value == "display") {
                            if (controllerButton.attributes.buttons.value == 1){
                                controllerButton.style.display = "block";
                            } else {
                                controllerButton.style.display = "none";
                            }
                        } else {
                            controllerButton.style.left = `calc(50% + ${controllerButton.attributes.posLeftX.value}px)`;
                            controllerButton.style.top = `calc(50% + ${controllerButton.attributes.posLeftY.value}px)`;
                            controllerButton.style.transform = `rotate(${controllerButton.attributes.rotationLeft.value}deg)`;
                        }
                        break;
                    case right:
                        if (controllerButton.attributes.mode.value == "display") {
                            if (controllerButton.attributes.buttons.value == 2){
                                controllerButton.style.display = "block";
                            } else {
                                controllerButton.style.display = "none";
                            }
                        } else {
                            controllerButton.style.left = `calc(50% + ${controllerButton.attributes.posRightX.value}px)`;
                            controllerButton.style.top = `calc(50% + ${controllerButton.attributes.posRightY.value}px)`;
                            controllerButton.style.transform = `rotate(${controllerButton.attributes.rotationRight.value}deg)`;
                        }
                        break;
                    default:
                        if (controllerButton.attributes.mode.value == "display") {
                            if (controllerButton.attributes.buttons.value == 0){
                                controllerButton.style.display = "block";
                            } else {
                                controllerButton.style.display = "none";
                            }
                        } else {
                            controllerButton.style.left = `calc(50% + 0px)`;
                            controllerButton.style.top = `calc(50% + 0px)`;
                            controllerButton.style.transform = `rotate(0deg)`;
                        }
                        break;
                }

            });
        }

        await new Promise(r => setTimeout(r, 1000/60));
    }
}

// Function to handle the mouse down event
function onMouseDown(event) {
  isDragging = true;
  initialMouseX = event.clientX;
  initialMouseY = event.clientY;
  // Initialize mouse movement offsets with the current position
  mouseMovementX = 0;
  mouseMovementY = 0;

  // Add "grabbing" cursor style
  moveContainer.style.cursor = "grabbing";
}

// Function to handle the mouse move event
function onMouseMove(event) {
   if (!isDragging) return;

  const deltaX = event.clientX - initialMouseX;
  const deltaY = event.clientY - initialMouseY;

  // Apply the new position to each image separately while preserving their existing offset
  const images = imageContainer.querySelectorAll("img");
  images.forEach((img) => {
    const imgLeft = img.style.left;
    const imgTop = img.style.top;
    console.log(imgLeft + " " + imgTop)
    const newLeft = `calc(${imgLeft} + ${deltaX}px)`;
    const newTop = `calc(${imgTop} + ${deltaY}px)`;
    img.style.left = `${newLeft}`;
    img.style.top = `${newTop}`;
  });

  // Update the initial mouse position
  initialMouseX = event.clientX;
  initialMouseY = event.clientY;
}

// Function to handle the mouse up event
function onMouseUp() {
  isDragging = false;
  // Restore the default cursor style
  moveContainer.style.cursor = "grab";
}

// Function to prevent the default drag behavior
function preventDefaultDrag(event) {
  event.preventDefault();
}

// Add event listeners for mouse events on the move-container
document.addEventListener("mousedown", onMouseDown);
document.addEventListener("mousemove", onMouseMove);
document.addEventListener("mouseup", onMouseUp);

// Add an event listener to prevent default drag behavior on the move-container
moveContainer.addEventListener("dragstart", preventDefaultDrag);

// Control the listening for gamepads
window.addEventListener("gamepadconnected", (e) => {
    pool();
});
