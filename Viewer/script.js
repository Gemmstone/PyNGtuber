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

async function cursorPosition(X, Y){
    var cursor_divs = document.querySelectorAll(".cursor_div");
    if(cursor_divs.length > 0) {
        cursor_divs.forEach(function(cursor_div) {
            if(cursor_div.attributes.track_mouse_x.value == 1){
                if(cursor_div.attributes.invert_mouse_x.value == 1){
                    cursor_div.style.left = `calc(50% + ${X * cursor_div.attributes.cursorScaleX.value * -1}px)`;
                } else {
                    cursor_div.style.left = `calc(50% + ${X * cursor_div.attributes.cursorScaleX.value}px)`;
                }
            }
            if(cursor_div.attributes.track_mouse_y.value == 1){
                if(cursor_div.attributes.invert_mouse_y.value == 1){
                    cursor_div.style.top = `calc(50% - ${Y * (cursor_div.attributes.cursorScaleY.value * 2)}px)`;
                } else {
                    cursor_div.style.top = `calc(50% - ${Y * (cursor_div.attributes.cursorScaleY.value * 2) * -1}px)`;
                }
            }
        });
    }
}

async function pool(){
    // while(true){

    // Wheel / stick control X
    var controllerWheels = document.querySelectorAll(".controller_wheelX");
    if(controllerWheels.length > 0) {
        controllerWheels.forEach(function(controllerWheel) {

            let rawx = navigator.getGamepads()[controllerWheel.attributes.player.value].axes[controllerWheel.attributes.invertAxis.value == 0 ? 0 : 1]
            let x = 0
            if(rawx > controllerWheel.attributes.deadzone.value)
                x = rawx-controllerWheel.attributes.deadzone.value/(1-controllerWheel.attributes.deadzone.value)
            else if(rawx < -controllerWheel.attributes.deadzone.value)
                x = rawx-controllerWheel.attributes.player.value/(1-controllerWheel.attributes.deadzone.value)
            // console.log(x, controllerWheel.attributes.deg.value);
            let rotation = x * controllerWheel.attributes.deg.value;

            var currentTransform = controllerWheel.style.transform;
            var currentRotate = 0;
            if(currentTransform && currentTransform.includes("rotateZ")) {
                var rotateIndex = currentTransform.indexOf("rotateZ");
                var endIndex = currentTransform.indexOf("deg", rotateIndex);
                currentRotate = parseFloat(currentTransform.substring(rotateIndex + 8, endIndex));
            }
            controllerWheel.style.transform = currentTransform.replace(`rotateZ(${currentRotate}deg)`, `rotateZ(${rotation}deg)`);
        });
    };

    // Wheel / stick control Y
    var controllerWheelsY = document.querySelectorAll(".controller_wheelY");
    if(controllerWheelsY.length > 0) {
        controllerWheelsY.forEach(function(controllerWheelY) {

            let rawy = navigator.getGamepads()[controllerWheelY.attributes.player.value].axes[controllerWheelY.attributes.invertAxis.value == 0 ? 1 : 0]
            let x = 0
            if(rawy > controllerWheelY.attributes.deadzone.value)
                x = rawy-controllerWheelY.attributes.deadzone.value/(1-controllerWheelY.attributes.deadzone.value)
            else if(rawy < -controllerWheelY.attributes.deadzone.value)
                x = rawy-controllerWheelY.attributes.player.value/(1-controllerWheelY.attributes.deadzone.value)
            let rotation = x * controllerWheelY.attributes.deg.value;

            var currentTransform = controllerWheelY.style.transform;
            var currentRotate = 0;

            if (currentTransform && currentTransform.includes("rotateX")) {
                var rotateIndex = currentTransform.indexOf("rotateX");
                var endIndex = currentTransform.indexOf("deg", rotateIndex);
                currentRotate = parseFloat(currentTransform.substring(rotateIndex + 8, endIndex));
            }

            controllerWheelY.style.transform = currentTransform.replace(`rotateX(${currentRotate}deg)`, `rotateX(${rotation}deg)`);

            var currentTransform = controllerWheelY.style.transform;
            var currentScale = 1; // Assuming initial scale is 100%

            if (currentTransform && currentTransform.includes("scale")) {
                var scaleIndex = currentTransform.indexOf("scale");
                var endIndex_scale = currentTransform.indexOf(")", scaleIndex) + 2;
                currentScale = parseFloat(currentTransform.substring(scaleIndex + 6, endIndex_scale));
            }

            controllerWheelY.style.transform = controllerWheelY.style.transform.replace(
                `scale(${currentScale})`, `scale(${100 + rotation}%)`
            );

            if (rotation > 0){
                controllerWheelY.style.top = `calc(50% + ${rotation * 2}px)`;
            } else {
                controllerWheelY.style.top = `calc(50% + ${rotation * 3}px)`;
            }
        });
    };

    // Whammy / stick control X
    var controllerWhammyWheels = document.querySelectorAll(".Whammywheel");
    if(controllerWhammyWheels.length > 0) {
        controllerWhammyWheels.forEach(function(controllerWhammyWheel) {

            let rawx = navigator.getGamepads()[controllerWhammyWheel.attributes.player.value].axes[controllerWhammyWheel.attributes.invertAxis.value == 0 ? 2 : 3]
            let x = 0
            if(rawx > controllerWhammyWheel.attributes.deadzone.value)
                x = rawx-controllerWhammyWheel.attributes.deadzone.value/(1-controllerWhammyWheel.attributes.deadzone.value)
            else if(rawx < -controllerWhammyWheel.attributes.deadzone.value)
                x = rawx-controllerWhammyWheel.attributes.player.value/(1-controllerWhammyWheel.attributes.deadzone.value)
            let rotation = x * controllerWhammyWheel.attributes.deg.value;

            var currentTransform = controllerWhammyWheel.style.transform;
            var currentRotate = 0;
            if(currentTransform && currentTransform.includes("rotateZ")) {
                var rotateIndex = currentTransform.indexOf("rotateZ");
                var endIndex = currentTransform.indexOf("deg", rotateIndex);
                currentRotate = parseFloat(currentTransform.substring(rotateIndex + 8, endIndex));
            }
            controllerWhammyWheel.style.transform = currentTransform.replace(`rotateZ(${currentRotate}deg)`, `rotateZ(${rotation}deg)`);
        });
    };

    // Wheel / stick 2 control X and Y
    var controllerWheelsZ = document.querySelectorAll(".controller_wheelZ");
    if(controllerWheelsZ.length > 0) {
        controllerWheelsZ.forEach(function(controllerWheelZ) {

            let rawx = navigator.getGamepads()[controllerWheelZ.attributes.player.value].axes[controllerWheelZ.attributes.invertAxis.value == 0 ? 2 : 3]

            let x = 0
            if(rawx > controllerWheelZ.attributes.deadzone.value)
                x = rawx-controllerWheelZ.attributes.deadzone.value/(1-controllerWheelZ.attributes.deadzone.value)
            else if(rawx < -controllerWheelZ.attributes.deadzone.value)
                x = rawx-controllerWheelZ.attributes.player.value/(1-controllerWheelZ.attributes.deadzone.value)
            let rotationx = x * controllerWheelZ.attributes.deg.value;

            let rawy = navigator.getGamepads()[controllerWheelZ.attributes.player.value].axes[controllerWheelZ.attributes.invertAxis.value == 0 ? 3 : 2]
            let y = 0
            if(rawy > controllerWheelZ.attributes.deadzone.value)
                y = rawy-controllerWheelZ.attributes.deadzone.value/(1-controllerWheelZ.attributes.deadzone.value)
            else if(rawy < -controllerWheelZ.attributes.deadzone.value)
                y = rawy-controllerWheelZ.attributes.player.value/(1-controllerWheelZ.attributes.deadzone.value)
            let rotationy = y * controllerWheelZ.attributes.deg.value;

            var currentTransform = controllerWheelZ.style.transform;
            var currentRotate = 0;

            if (currentTransform && currentTransform.includes("rotateY")) {
                var rotateIndex = currentTransform.indexOf("rotateY");
                var endIndex = currentTransform.indexOf("deg", rotateIndex);
                currentRotate = parseFloat(currentTransform.substring(rotateIndex + 8, endIndex));
            }

            controllerWheelZ.style.transform = currentTransform.replace(
                `rotateY(${currentRotate}deg)`, `rotateY(${rotationx}deg)`
            );

            controllerWheelZ.style.left = `calc(50% + ${rotationx}px)`;
            controllerWheelZ.style.top = `calc(50% - ${rotationy}px)`;

        });
    };

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

    // Guitar control
    var guitarButtons = document.querySelectorAll(".guitar_buttons");
    // console.log(guitarButtons.length);
    if(guitarButtons.length > 0) {
        guitarButtons.forEach(function(guitarButton) {
            let buttons = navigator.getGamepads()[guitarButton.attributes.player.value].buttons

            let up = false
            let down = false

            let green = false
            let red = false
            let yellow = false
            let blue = false
            let orange = false

            /* This was made for the PS4 controller

            for(let i = 0; i < buttons.length; i++){
                if(buttons[i].pressed){
                    if(!up && i == 12){
                        up = true
                    }else if(!down && i == 13){
                        down = true
                    }else if(!green && i == 5){
                        green = true
                    }else if(!red && i == 1){
                        red = true
                    }else if(!yellow && i == 3){
                        yellow = true
                    }else if(!blue && i == 0){
                        blue = true
                    }else if(!orange && i == 2){
                        orange = true
                    }
                }
            }

            */
            let rawx = navigator.getGamepads()[guitarButton.attributes.player.value].axes[9]

            if(!up && parseInt(rawx) == -1){
                up = true
            }else if(!down && parseInt(rawx) == 0){
                down = true
            }

            for(let i = 0; i < buttons.length; i++){
                if(buttons[i].pressed){
                    if(!green && i == 1){
                        green = true
                    }else if(!red && i == 2){
                        red = true
                    }else if(!yellow && i == 0){
                        yellow = true
                    }else if(!blue && i == 3){
                        blue = true
                    }else if(!orange && i == 4){
                        orange = true
                    }
                }
            }

            switch(true){
                case up:
                    guitarButton.style.left = `calc(50% + ${guitarButton.attributes.posGuitarUpX.value}px)`;
                    guitarButton.style.top = `calc(50% + ${guitarButton.attributes.posGuitarUpY.value}px)`;
                    guitarButton.style.transform = `rotate(${guitarButton.attributes.rotationGuitarUp.value}deg)`;
                    break;
                case down:
                    guitarButton.style.left = `calc(50% + ${guitarButton.attributes.posGuitarDownX.value}px)`;
                    guitarButton.style.top = `calc(50% + ${guitarButton.attributes.posGuitarDownY.value}px)`;
                    guitarButton.style.transform = `rotate(${guitarButton.attributes.rotationGuitarDown.value}deg)`;
                    break;
                default:
                    guitarButton.style.left = `calc(50% + 0px)`;
                    guitarButton.style.top = `calc(50% + 0px)`;
                    guitarButton.style.transform = `rotate(0deg)`;
                    break;
            }

            let chordsString = guitarButton.attributes.chords.value;

            // Check if the chordsString is empty
            if (chordsString) {
                let colorsList = chordsString.split(',').map(color => color.trim());

                if (colorsList.includes("None")) {
                    if (green || red || yellow || blue || orange) {
                        guitarButton.style.display = "none";
                    } else {
                        guitarButton.style.display = "block";
                    }
                } else {
                    let allColorsTrue = colorsList.every(color => {
                        let variableName = color.toLowerCase();
                        return eval(variableName);
                    });

                    if (allColorsTrue) {
                        guitarButton.style.display = "block";
                    } else {
                        guitarButton.style.display = "none";
                    }
                }
            }

        });
    }

    // await new Promise(r => setTimeout(r, 1000/60));
    window.requestAnimationFrame(pool)
    // }
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
    const imgTop = img.style.top
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
var controller1 = document.querySelectorAll(".controller_wheelX");
var controller2 = document.querySelectorAll(".controller_wheelY");
var controller3 = document.querySelectorAll(".Whammywheel");
var controller4 = document.querySelectorAll(".controller_wheelZ");
var controller5 = document.querySelectorAll(".controller_buttons");
var controller6 = document.querySelectorAll(".guitar_buttons");

var controllers = controller1.length + controller2.length + controller3.length + controller4.length + controller5.length + controller6.length
// console.log("controllers:" + controllers);
if(controllers > 0){
    window.addEventListener("gamepadconnected", (e) => {
        // pool();
        window.requestAnimationFrame(pool)
    });
}