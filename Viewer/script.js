const container = document.getElementById("images_container");

const stage = new Konva.Stage({
    container: 'image-wrapper',
    x: window.innerWidth / 2,
    y: window.innerHeight / 2
});
stage.offsetX(window.innerWidth / 2);
stage.offsetY(window.innerHeight / 2);

const runningAnimations = new Map(); // To keep track of running animations

const leftButtons = [4,6,8,10,12,13,14,15];
const rightButtons = [0,1,2,3,5,7,9,11];
const True = true;
const False = false;
const None = null;

let mouseMovementX = 0;
let mouseMovementY = 0;

let serverAddress = null;

// Function to establish WebSocket connection
function connectWebSocket() {
    if (!serverAddress) {
        // console.error('WebSocket server address not provided');
        return;
    }
    document.body.style.backgroundColor = "transparent";

    const socket = new WebSocket(`ws://${serverAddress}`);

    socket.addEventListener('open', function (event) {
        socket.send('reload images')
    });

    socket.addEventListener('message', function (event) {
        console.log('Message from server:', event.data);

        try {
            const result = eval(event.data);
        } catch (error) {
            console.error('Error evaluating JavaScript:', error);
        }
    });

    socket.addEventListener('error', function (event) {
        console.error('PyNGtuber WebSocket error:', event);
    });

    socket.addEventListener('close', function (event) {
        console.log('PyNGtuber connection closed');
        setTimeout(connectWebSocket, 2000);
    });
}

// Get the URL parameters
const urlParams = new URLSearchParams(window.location.search);
serverAddress = urlParams.get('server_address');

// Initial connection attempt
connectWebSocket();

async function update_images(htmlContent) {
    document.getElementById('image-wrapper').innerHTML = htmlContent;
    var editing_divs = document.getElementsByClassName("editing_div");
    for (var i = 0; i < editing_divs.length; i++) {
        if (!serverAddress) {
            var className = editing_divs[i].getAttribute('editing');
        } else {
            var className = editing_divs[i].getAttribute('default');
        }
        editing_divs[i].classList.add(className);
    }
}

function get(object, key, defaultValue) {
    return key in object ? object[key] : defaultValue;
}

async function flip_canvas(valueH, valueV, seg, timing) {
    document.body.style.transition = `all ${seg}s ${timing}`;
    document.body.style.transform = `rotateY(${valueH}deg) rotateX(${valueV}deg)`;
}

function applyAnimation(animationName, image, config, destroy = false) {
    const imageId = image._id;

    // Default state (optional, used if resetting to default is needed)
    const defaultState = {
        x: window.innerWidth / 2,
        y: window.innerHeight / 2,
        scaleX: 1,
        scaleY: 1,
        rotation: 0,
        opacity: 1
    };

    if (runningAnimations.has(imageId)) {
        const currentAnimation = runningAnimations.get(imageId);

        if (destroy) {
            currentAnimation.finish();
             return null;
        }

        if (currentAnimation.name === animationName && JSON.stringify(currentAnimation.config) === JSON.stringify(config)) {
            return null;
        } else {
            currentAnimation.finish();
        }
    }

    if (animations.hasOwnProperty(animationName)) {
        const newAnimation = new animations[animationName](image, config);
        newAnimation.name = animationName;
        newAnimation.config = config;
        runningAnimations.set(imageId, newAnimation);
        newAnimation.play();
        return newAnimation;
    } else {
        console.error(`Animation '${animationName}' is not defined.`);
        return null
    }
}

async function update_mic(status, animation, speed, direction, pacing, iteration, performance) {
    var elements = document.getElementsByClassName("talking");
    var elements_not_being_edited = document.getElementsByClassName("talking_not_being_edited");
    var elements_being_edited = document.getElementsByClassName("talking_being_edited");
    var imageWrapper = document.querySelectorAll(".idle_animation");
    var assets = document.getElementsByClassName("asset");
    var imageAddedWrapper = document.querySelectorAll(".added_animation");

    var stateMap = {
        0: "talking_closed",
        1: "talking_open",
        2: "talking_screaming"
    };

    for (var i = 0; i < elements.length; i++) {
        var states = elements[i].attributes.talking.value.split(" ");
        elements[i].style.transition = "opacity 0.2s";
        elements[i].style.opacity = (states.includes(stateMap[status])) ? 1 : 0;
    }

    for (var i = 0; i < elements_not_being_edited.length; i++) {
        var states = elements_not_being_edited[i].attributes.talking.value.split(" ");
        elements_not_being_edited[i].style.transition = "opacity 0.2s";
        elements_not_being_edited[i].style.opacity = (states.includes(stateMap[status])) ? 0.7 : 0.3;
    }

    for (var i = 0; i < elements_being_edited.length; i++) {
        var states = elements_being_edited[i].attributes.talking.value.split(" ");
        elements_being_edited[i].style.transition = "opacity 0.2s";
        elements_being_edited[i].style.opacity = (states.includes(stateMap[status])) ? 1 : 0.5;
    }

    if(imageWrapper.length > 0) {
        imageWrapper.forEach(function(image) {
            iteration = (iteration == 0) ? "infinite" : iteration;
            image.style.animation = `${animation} ${speed}s ${pacing} ${iteration}`;
            image.style.animationDirection = direction;
        });
    }

    if (!performance) {
        if(imageAddedWrapper.length > 0) {
            imageAddedWrapper.forEach(function(animation_div) {
                switch(status) {
                    case 2:
                        animation = animation_div.attributes.animation_name_screaming.value;
                        speed = animation_div.attributes.animation_speed_screaming.value;
                        direction = animation_div.attributes.animation_direction_screaming.value;
                        pacing = animation_div.attributes.animation_pacing_screaming.value;
                        iteration = animation_div.attributes.animation_iteration_screaming.value;
                        break;
                    case 1:
                        animation = animation_div.attributes.animation_name_talking.value;
                        speed = animation_div.attributes.animation_speed_talking.value;
                        direction = animation_div.attributes.animation_direction_talking.value;
                        pacing = animation_div.attributes.animation_pacing_talking.value;
                        iteration = animation_div.attributes.animation_iteration_talking.value;
                        break;
                    default:
                        animation = animation_div.attributes.animation_name_idle.value;
                        speed = animation_div.attributes.animation_speed_idle.value;
                        direction = animation_div.attributes.animation_direction_idle.value;
                        pacing = animation_div.attributes.animation_pacing_idle.value;
                        iteration = animation_div.attributes.animation_iteration_idle.value;
                }
                iteration = (iteration == 0) ? "infinite" : iteration;
                animation_div.style.animation = `${animation} ${speed}s ${pacing} ${iteration}`;
                animation_div.style.animationDirection = direction;
            });
        }

        if(assets.length > 0) {
            for (var i = 0; i < assets.length; i++) {
                switch(status) {
                    case 2:
                        sizeX = assets[i].attributes.sizeX_screaming.value;
                        sizeY = assets[i].attributes.sizeY_screaming.value;
                        posX = assets[i].attributes.posX_screaming.value;
                        posY = assets[i].attributes.posY_screaming.value;
                        rotation = assets[i].attributes.rotation_screaming.value;
                        speed = assets[i].attributes.screaming_position_speed.value;
                        pacing = assets[i].attributes.screaming_position_pacing.value;
                        break;
                    case 1:
                        sizeX = assets[i].attributes.sizeX_talking.value;
                        sizeY = assets[i].attributes.sizeY_talking.value;
                        posX = assets[i].attributes.posX_talking.value;
                        posY = assets[i].attributes.posY_talking.value;
                        rotation = assets[i].attributes.rotation_talking.value;
                        speed = assets[i].attributes.talking_position_speed.value;
                        pacing = assets[i].attributes.talking_position_pacing.value;
                        break;
                    default:
                        sizeX = assets[i].attributes.sizeX.value;
                        sizeY = assets[i].attributes.sizeY.value;
                        posX = assets[i].attributes.posX.value;
                        posY = assets[i].attributes.posY.value;
                        rotation = assets[i].attributes.rotation.value;
                        speed = assets[i].attributes.idle_position_speed.value;
                        pacing = assets[i].attributes.idle_position_pacing.value;
                }
                assets[i].style.transition = `all ${speed}s ${pacing}`;
                assets[i].style.left = `calc(50% + ${posX}px)`;
                assets[i].style.top = `calc(50% + ${posY}px)`;
                assets[i].style.width = `calc(50% + ${sizeX}px)`;
                assets[i].style.height = `calc(50% + ${sizeY}px)`;
                assets[i].style.transition = `all ${speed}s ${pacing}`;
                assets[i].style.transform = `translate(-50%, -50%) rotate(${rotation}deg)`;
            }
        }
    }
}

async function cursorPosition(X, Y, forced, pacing, speed) {
    var cursor_divs = document.querySelectorAll(".cursor_div");
    if(cursor_divs.length > 0) {
        cursor_divs.forEach(function(cursor_div) {
            if (forced == cursor_div.attributes.forced_mouse_tracking.value) {
                cursor_div.style.transition = `all ${speed}s ${pacing}`;
                if(cursor_div.attributes.track_mouse_x.value == 1){
                    if(cursor_div.attributes.invert_mouse_x.value == 1){
                        cursor_div.style.left = `calc(50% + ${X * cursor_div.attributes.cursorScaleX.value * -1}px)`;
                    } else {
                        cursor_div.style.left = `calc(50% + ${X * cursor_div.attributes.cursorScaleX.value}px)`;
                    }
                }
                cursor_div.style.transition = `all ${speed}s ${pacing}`;
                if(cursor_div.attributes.track_mouse_y.value == 1){
                    if(cursor_div.attributes.invert_mouse_y.value == 1){
                        cursor_div.style.top = `calc(50% - ${Y * (cursor_div.attributes.cursorScaleY.value * 2)}px)`;
                    } else {
                        cursor_div.style.top = `calc(50% - ${Y * (cursor_div.attributes.cursorScaleY.value * 2) * -1}px)`;
                    }
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
                controllerWheelY.style.top = `calc(50% + ${rotation}px)`;
            } else {
                controllerWheelY.style.top = `calc(50% + ${rotation * -1}px)`;
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
                        controllerButton.style.transition = 'all 0.2s ease-in-out';
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
                        controllerButton.style.transition = 'all 0.2s ease-in-out';
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
                        controllerButton.style.transition = 'all 0.2s ease-in-out';
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
                        controllerButton.style.transition = 'all 0.2s ease-in-out';
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
    window.requestAnimationFrame(pool)
}

function addImagesToCanvas(imageDataList, edited) {
    stage.width(window.innerWidth);
    stage.height(window.innerHeight);
    destroy_animations();
    stage.destroyChildren();

    const layer = new Konva.Layer({
        // draggable: true,
    });
    stage.add(layer);

    const center_x = window.innerWidth / 2;
    const center_y = window.innerHeight / 2;

    // Sort images by posZ to handle z-index
    imageDataList.sort((a, b) => a.posZ - b.posZ);

    const idleAnim = new Konva.Group({
        name: 'idle_animation',
        x: center_x,
        y: center_y,
    });
    idleAnim.offsetX(center_x);
    idleAnim.offsetY(center_y);

    layer.add(idleAnim);

    imageDataList.forEach((imageData, index) => {
        let parentElement = layer;

        // Add different types of animations and divs to the group
        if (get(imageData, 'animation_idle', true)){
            parentElement = idleAnim;
        }

        editing = "not_in_editor";
        if (edited !== null && !serverAddress) {
            if (edited.type === "general") {
                editing = imageData.routeOg.replace(/\\/g, "/").toLowerCase().includes(`assets/${edited.collection.toLowerCase()}/${edited.value.toLowerCase()}/`) ? "being_edited" : "not_being_edited";
            } else {
                editing = imageData.routeOg === edited.value ? "being_edited" : "not_being_edited";
            }

            const editionAnim = new Konva.Group({
                x: center_x,
                y: center_y,
                opacity: "being_edited" === editing ? 1 : 0.5
            });
            editionAnim.offsetX(center_x);
            editionAnim.offsetY(center_y);
            parentElement.add(editionAnim);
            parentElement = editionAnim;
        }

        if (get(imageData, 'animation_name_idle', true) || get(imageData, 'animation_name_talking', true)) {
            // Added animation div
            const addedAnim = new Konva.Group({
                name: 'added_animation',
                x: center_x,
                y: center_y,

                animation_name_idle: get(imageData, "animation_name_idle", "None"),
                animation_name_talking: get(imageData, "animation_name_talking", "None"),
                animation_name_screaming: get(imageData, "animation_name_screaming", get(imageData, "animation_name_talking", "None")),
                animation_speed_idle: get(imageData, "animation_speed_idle", 6),
                animation_speed_talking: get(imageData, "animation_speed_talking", 0.5),
                animation_speed_screaming: get(imageData, "animation_speed_screaming", get(imageData, "animation_speed_talking", 0.5)),
                animation_direction_idle: get(imageData, 'animation_direction_idle',  "normal"),
                animation_direction_talking: get(imageData, 'animation_direction_talking',  "normal"),
                animation_direction_screaming: get(imageData, 'animation_direction_screaming',  get(imageData, 'animation_direction_talking',  "normal")),
                animation_iteration_idle: get(imageData, "animation_iteration_idle", 0),
                animation_iteration_talking: get(imageData, "animation_iteration_talking", 0),
                animation_iteration_screaming: get(imageData, "animation_iteration_screaming", get(imageData, "animation_iteration_talking", 0))
            });
            addedAnim.offsetX(center_x);
            addedAnim.offsetY(center_y);

            parentElement.add(addedAnim);
            parentElement = addedAnim;
        }

        if (get(imageData, 'cursor', false)) {
            // Cursor div
            const cursorDiv = new Konva.Group({
                name: 'cursor_div',
                x: center_x,
                y: center_y,
                cursorScaleX: get(imageData, "cursorScaleX", get(imageData, "cursorScale", 0.01)),
                cursorScaleY: get(imageData, "cursorScaleY", get(imageData, "cursorScale", 0.01)),
                invert_mouse_x: get(imageData, "invert_mouse_x", 1),
                invert_mouse_y: get(imageData, "invert_mouse_y", 0),
                track_mouse_x: get(imageData, "track_mouse_x", 1),
                track_mouse_y: get(imageData, "track_mouse_y", 1),
                forced_mouse_tracking: get(imageData, "forced_mouse_tracking", 0)
            });
            cursorDiv.offsetX(center_x);
            cursorDiv.offsetY(center_y);

            parentElement.add(cursorDiv);
            parentElement = cursorDiv;
        }

        if ('controller' in imageData) {
            if (imageData.controller.includes('controller_buttons')) {
                // Controller buttons div
                const controllerButtonsDiv = new Konva.Group({
                    name: 'controller_buttons',
                    x: center_x,
                    y: center_y,

                    player: get(imageData, "player", 1) - 1,
                    mode: get(imageData, "mode", 'display'),
                    buttons: get(imageData, "buttons", 0),
                    posBothX: get(imageData, "posBothX", 0),
                    posBothY: get(imageData, "posBothY", 0),
                    rotationBoth: get(imageData, "rotationBoth", 0),
                    posLeftX: get(imageData, "posLeftX", 0),
                    posLeftY: get(imageData, "posLeftY", 0),
                    rotationLeft: get(imageData, "rotationLeft", 0),
                    posRightX: get(imageData, "posRightX", 0),
                    posRightY: get(imageData, "posRightY", 0),
                    rotationRight: get(imageData, "rotationRight", 0),

                    offsetX_var: center_x,
                    offsetY_var: center_y,
                });
                controllerButtonsDiv.offsetX(center_x);
                controllerButtonsDiv.offsetY(center_y);

                parentElement.add(controllerButtonsDiv);
                parentElement = controllerButtonsDiv;
            }

            if (imageData.controller.includes('guitar_buttons')) {
                // Guitar buttons div
                const guitarButtonsDiv = new Konva.Group({
                    name: 'guitar_buttons',
                    x: center_x,
                    y: center_y,

                    player: get(imageData, "player", 1) - 1,
                    chords: get(imageData, "chords", []).join(","),
                    posGuitarUpX: get(imageData, "posGuitarUpX", 0),
                    posGuitarUpY: get(imageData, "posGuitarUpY", 0),
                    rotationGuitarUp: get(imageData, "rotationGuitarUp", 0),
                    posGuitarDownX: get(imageData, "posGuitarDownX", 0),
                    posGuitarDownY: get(imageData, "posGuitarDownY", 0),
                    rotationGuitarDown: get(imageData, "rotationGuitarDown", 0),

                    offsetX_var: center_x,
                    offsetY_var: center_y,
                });
                guitarButtonsDiv.offsetX(center_x);
                guitarButtonsDiv.offsetY(center_y);

                parentElement.add(guitarButtonsDiv);
                parentElement = guitarButtonsDiv;
            }

            deg = get(imageData, 'deg', -90)
            if (imageData.controller.includes('controller_wheel')) {
                // Controller wheel divs
                const controllerWheelXDiv = new Konva.Group({
                    name: 'controller_wheelX',
                    x: center_x + get(imageData, 'originX', 0),
                    y: center_y + get(imageData, 'originY', 0),

                    player: get(imageData, "player2", 1) - 1,
                    deg: deg,
                    invertAxis: get(imageData, 'invertAxis', 0),
                    deadzone: get(imageData, "deadzone", 0.0550),

                    offsetX_var: center_x + get(imageData, 'originX', 0),
                    offsetY_var: center_y + get(imageData, 'originX', 0),
                });
                controllerWheelXDiv.offsetX(center_x + get(imageData, 'originX', 0));
                controllerWheelXDiv.offsetY(center_y + get(imageData, 'originY', 0));

                parentElement.add(controllerWheelXDiv);
                parentElement = controllerWheelXDiv;
            }

            if (imageData.controller.includes('controller_wheel')) {
                const controllerWheelYDiv = new Konva.Group({
                    name: 'controller_wheelY',
                    x: center_x + get(imageData, 'originXzoom', 0),
                    y: center_y + get(imageData, 'originYzoom', 0),

                    player: get(imageData, "player2", 1) - 1,
                    deg: get(imageData, 'degZoom', deg),
                    invertAxis: get(imageData, 'invertAxis', 0),
                    deadzone: get(imageData, "deadzone", 0.0550),

                    offsetX_var: center_x + get(imageData, 'originXzoom', 0),
                    offsetY_var: center_y + get(imageData, 'originYzoom', 0),
                });
                controllerWheelYDiv.offsetX(center_x + get(imageData, 'originXzoom', 0));
                controllerWheelYDiv.offsetY(center_y + get(imageData, 'originYzoom', 0));

                parentElement.add(controllerWheelYDiv);
                parentElement = controllerWheelYDiv;
            }

            if (imageData.controller.includes('controller_wheel')) {
                // Controller wheel divs
                const controllerWheelZDiv = new Konva.Group({
                    name: 'controller_wheelZ',
                    x: center_x + get(imageData, 'originXright', 0),
                    y: center_y + get(imageData, 'originYright', 0),

                    player: get(imageData, "player", 1) - 1,
                    deg: get(imageData, 'degRight', deg),
                    invertAxis: get(imageData, 'invertAxis', 0),
                    deadzone: get(imageData, "deadzone", 0.0550),

                    offsetX_var: center_x + get(imageData, 'originXright', 0),
                    offsetY_var: center_y + get(imageData, 'originYright', 0),
                });
                controllerWheelZDiv.offsetX(center_x + get(imageData, 'originXright', 0));
                controllerWheelZDiv.offsetY(center_y + get(imageData, 'originYright', 0));

                parentElement.add(controllerWheelZDiv);
                parentElement = controllerWheelZDiv;
            }

            if (imageData.controller.includes('controller_wheel')) {
                // Controller wheel divs
                const controller_wheelWhammy_div = new Konva.Group({
                    name: 'Whammywheel',
                    x: center_x + get(imageData, 'originXwhammy', 0),
                    y: center_y + get(imageData, 'originYwhammy', 0),

                    player: get(imageData, "player", 1) - 1,
                    deg: get(imageData, 'degWhammy', 0),
                    invertAxis: get(imageData, 'invertAxis', 0),
                    deadzone: get(imageData, "deadzone", 0.0550),

                    offsetX_var: center_x + get(imageData, 'originXwhammy', 0),
                    offsetY_var: center_y + get(imageData, 'originYwhammy', 0),
                });
                controller_wheelWhammy_div.offsetX(center_x + get(imageData, 'originXwhammy', 0));
                controller_wheelWhammy_div.offsetY(center_y + get(imageData, 'originYwhammy', 0));

                parentElement.add(controller_wheelWhammy_div);
                parentElement = controller_wheelWhammy_div;
            }
        }

        var blinking = get(imageData, 'blinking', ["ignore"])
        if (blinking !== "ignore" && !blinking.includes("ignore")) {
            // Blinking animation div
            const blinkingDiv = new Konva.Group({
                name: blinking,
                x: center_x,
                y: center_y,
                opacity: blinking.includes("blinking_closed") ? 1 : 0
            });
            blinkingDiv.offsetX(center_x);
            blinkingDiv.offsetY(center_y);

            parentElement.add(blinkingDiv);
            parentElement = blinkingDiv;
        }

        var talking = get(imageData, 'talking', ["ignore"])
        if (!Array.isArray(talking)) {
            talking = [talking];
        }
        if (talking != "ignore" && !talking.includes("ignore")) {
            const talkingDiv = new Konva.Group({
                name: 'talking',
                x: center_x,
                y: center_y,
                talking: talking.join(" "),
                opacity: talking.includes("talking_closed") ? 1 : 0
            });
            talkingDiv.offsetX(center_x);
            talkingDiv.offsetY(center_y);

            parentElement.add(talkingDiv);
            parentElement = talkingDiv;
        }

        var sizeX = get(imageData, 'sizeX', 0);
        var sizeY = get(imageData, 'sizeY', 0);
        var posX = get(imageData, 'posX', 600);
        var posY = get(imageData, 'posY', 600);
        var rotation = get(imageData, 'rotation', 0);

        var move = "0";
        var moveToIDLE = "0";
        var moveToTALKING = "0";
        var moveToSCREAMING = "0";
        var move = get(imageData, 'move', False) ? "1" : "0";
        var moveToIDLE = get(imageData, 'moveToIDLE', True) ? "1" : "0";
        var moveToTALKING = get(imageData, 'moveToTALKING', True) ? "1" : "0";
        var moveToSCREAMING = get(imageData, 'moveToSCREAMING', True) ? "1" : "0";

        var idle_position_pacing = get(imageData, 'idle_position_pacing', "ease-in-out");
        var idle_position_speed = get(imageData, 'idle_position_speed', 0.2);

        var sizeX_talking = get(imageData, 'sizeX_talking', sizeX);
        var sizeY_talking = get(imageData, 'sizeY_talking', sizeY);
        var posX_talking = get(imageData, 'posX_talking', posX);
        var posY_talking = get(imageData, 'posY_talking', posY);
        var rotation_talking = get(imageData, 'rotation_talking', rotation);

        var talking_position_pacing = get(imageData, 'talking_position_pacing', idle_position_pacing);
        var talking_position_speed = get(imageData, 'talking_position_speed', idle_position_speed);

        var sizeX_screaming = get(imageData, 'sizeX_screaming', sizeX_talking);
        var sizeY_screaming = get(imageData, 'sizeY_screaming', sizeY_talking);
        var posX_screaming = get(imageData, 'posX_screaming', posX_talking);
        var posY_screaming = get(imageData, 'posY_screaming', posY_talking);
        var rotation_screaming = get(imageData, 'rotation_screaming', rotation_talking);

        var screaming_position_pacing = get(imageData, 'screaming_position_pacing', talking_position_pacing);
        var screaming_position_speed = get(imageData, 'screaming_position_speed', talking_position_speed);

        if (imageData.route.endsWith('.gif')) {
            var imageObj = document.createElement('canvas');

            gifler( window.location.protocol === "file:" ? imageData.route : imageData.routeRemote ).frames(imageObj, (ctx, frame) => {
                imageObj.width = frame.width;
                imageObj.height = frame.height;
                ctx.drawImage(frame.buffer, 0, 0);
                layer.draw();
            });
        } else {
            // Handle regular images
            var imageObj = new Image();
            imageObj.src = window.location.protocol === "file:" ? imageData.route : imageData.routeRemote;
        }

        let shadowProperties = {};
        if ("being_edited" == editing) {
            shadowProperties = {
                shadowColor: 'black',
                shadowBlur: 20,
                shadowOffset: { x: 0, y: 0 },
                shadowOpacity: 1,
            };
        } else if (get(imageData, "shadow", false)) {
            shadowProperties = {
                shadowColor: get(imageData, "color", "#000000"),
                shadowBlur: get(imageData, "shadowBlur", 20) / 2,
                shadowOffset: { x: get(imageData, "shadowX", 0), y: get(imageData, "shadowY", 0) * -1 },
                shadowOpacity: get(imageData, "shadowOpacity", 100) / 100,
            };
        }

        let opacityProperties = {};
        const opacity = get(imageData, "opacity", 100) / 100;
        if (opacity !== 1 && get(imageData, "filters", false)) {
            opacityProperties = {
                opacity: opacity,
            };
        }

        const blend = get(imageData, "blend", "source-over");
        blend_mode = {}
        if (blend !== "source-over" && get(imageData, "filters", false)){
            blend_mode = {
                globalCompositeOperation: blend,
            }
        }

        const konvaImage = new Konva.Image({
            x: center_x + get(imageData, "posX", 0),
            y: center_y + get(imageData, "posY", 0),
            name: editing,
            image: imageObj,
            width: imageData.sizeX,
            height: imageData.sizeY,
            rotation: imageData.rotation,
            ...blend_mode,
            ...opacityProperties,
            ...shadowProperties,
            sizeX: sizeX,
            sizeY: sizeY,
            posX: posX,
            posY: posY,
            rotationIDLE: rotation,
            move: move,
            moveToIDLE: moveToIDLE,
            moveToTALKING: moveToTALKING,
            moveToSCREAMING: moveToSCREAMING,
            move: move,
            moveToIDLE: moveToIDLE,
            moveToTALKING: moveToTALKING,
            moveToSCREAMING: moveToSCREAMING,
            idle_position_pacing: idle_position_pacing,
            idle_position_speed: idle_position_speed,
            sizeX_talking: sizeX_talking,
            sizeY_talking: sizeY_talking,
            posX_talking: posX_talking,
            posY_talking: posY_talking,
            rotation_talking: rotation_talking,
            talking_position_pacing: talking_position_pacing,
            talking_position_speed: talking_position_speed,
            sizeX_screaming: sizeX_screaming,
            sizeY_screaming: sizeY_screaming,
            posX_screaming: posX_screaming,
            posY_screaming: posY_screaming,
            rotation_screaming: rotation_screaming,
            screaming_position_pacing: screaming_position_pacing,
            screaming_position_speed: screaming_position_speed
        });

        if (get(imageData, "filters", false)) {
            let filters = [];

            const hue = get(imageData, "hue", 0);
            const saturation = get(imageData, "saturation", 0) / 2;
            const lightness = get(imageData, "brightness", 0) / 10;
            const contrast = get(imageData, "contrast", 0);
            const blur = get(imageData, "blur", 0) / 2;
            const pixelate = get(imageData, "pixelate", 0);
            const grayscale = get(imageData, "grayscale", false);
            const invert = get(imageData, "invert", false);

            if (hue !== 0 || saturation !== 0 || lightness !== 0) filters.push(Konva.Filters.HSL);
            if (contrast !== 0) filters.push(Konva.Filters.Contrast)
            if (blur !== 0) filters.push(Konva.Filters.Blur);
            if (pixelate !== 0) filters.push(Konva.Filters.Pixelate);
            if (grayscale) filters.push(Konva.Filters.Grayscale);
            if (invert) filters.push(Konva.Filters.Invert);

            konvaImage.cache();
            konvaImage.filters(filters);

            if (filters.includes(Konva.Filters.HSL)) {
                konvaImage.hue(hue);
                konvaImage.saturation(saturation);
                konvaImage.luminance(lightness);
            }
            if (filters.includes(Konva.Filters.Contrast)) konvaImage.contrast(contrast);
            if (filters.includes(Konva.Filters.Blur)) konvaImage.blurRadius(blur);
            if (filters.includes(Konva.Filters.Pixelate)) konvaImage.pixelSize(pixelate);
        }

        konvaImage.offsetX(konvaImage.width() / 2);
        konvaImage.offsetY(konvaImage.height() / 2);

        parentElement.add(konvaImage);
        konvaImage.animationData = imageData;
    });

    layer.draw();
    startAnimations();
}

// Function to handle the mouse down event
/*function onMouseDown(event) {
  isDragging = true;
  initialMouseX = event.clientX;
  initialMouseY = event.clientY;
  // Initialize mouse movement offsets with the current position
  mouseMovementX = 0;
  mouseMovementY = 0;

  // Add "grabbing" cursor style
  moveContainer.style.cursor = "grabbing";
}/*

// Function to handle the mouse move event
/*function onMouseMove(event) {
   if (!isDragging) return;

  const deltaX = event.clientX - initialMouseX;
  const deltaY = event.clientY - initialMouseY;

  // Apply the new position to each image separately while preserving their existing offset
  // const images = imageContainer.querySelectorAll("img");
  const images = imageContainer.querySelectorAll(".asset");
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
}*/

// Function to handle the mouse up event
/*function onMouseUp() {
  isDragging = false;
  // Restore the default cursor style
  moveContainer.style.cursor = "grab";
}*/

// Function to prevent the default drag behavior
function preventDefaultDrag(event) {
  event.preventDefault();
}

container.addEventListener("dragstart", preventDefaultDrag);

// Control the listening for gamepads
var controller1 = document.querySelectorAll(".controller_wheelX");
var controller2 = document.querySelectorAll(".controller_wheelY");
var controller3 = document.querySelectorAll(".Whammywheel");
var controller4 = document.querySelectorAll(".controller_wheelZ");
var controller5 = document.querySelectorAll(".controller_buttons");
var controller6 = document.querySelectorAll(".guitar_buttons");

// var controllers = controller1.length + controller2.length + controller3.length + controller4.length + controller5.length + controller6.length
// console.log("controllers:" + controllers);
//if(controllers > 0){
window.addEventListener("gamepadconnected", (e) => {
    window.requestAnimationFrame(pool)
});

function resolveAfter(seconds) {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve('resolved');
    }, seconds * 1000);
  });
}
