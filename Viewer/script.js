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
}

function get(object, key, defaultValue) {
    return key in object ? object[key] : defaultValue;
}

async function flip_canvas(valueH, valueV, seg, timing) {
    document.body.style.transition = `all ${seg}s ${timing}`;
    document.body.style.transform = `rotateY(${valueH}deg) rotateX(${valueV}deg)`;
    // document.body.style.transform = `rotateY(${valueH}deg) rotateZ(${valueV}deg)`;
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

async function update_mic(status, animation, speed, direction, easing, iteration, performance) {
    const stateMap = {
        0: "talking_closed",
        1: "talking_open",
        2: "talking_screaming"
    };

    const elements = stage.find('.talking');
    const imageWrapper = stage.find('.idle_animation');
    const imageAddedWrapper = stage.find('.added_animation');
    const assets = stage.find('Image');

    elements.forEach(function(group) {
        const states = group.getAttr('talking').split(" ");
        const targetOpacity = states.includes(stateMap[status]) ? 1 : 0;
        new Konva.Tween({
            node: group,
            duration: 0.1,
            opacity: targetOpacity
        }).play();
    });

    if (imageWrapper.length > 0) {
        imageWrapper.forEach(function(image, index) {
            let iterationCount = (iteration === 0) ? "infinite" : iteration;

            let anim = applyAnimation(animation, image, {
                speed: speed,
                iteration: iterationCount,
                direction: direction,
                center_x: window.innerWidth / 2,
                center_y: window.innerHeight / 2,
                easing: Konva.Easings[easing]
            });
        });
    }

    if (assets.length > 0) {
        assets.forEach(function(asset) {
            if (asset.getAttr('move') == 1) {
                var move, sizeX, sizeY, posX, posY, rotation, speed, pacing;
                switch (status) {
                    case 2:
                        move = asset.getAttr('moveToSCREAMING');
                        sizeX = asset.getAttr('sizeX_screaming');
                        sizeY = asset.getAttr('sizeY_screaming');
                        posX = asset.getAttr('posX_screaming');
                        posY = asset.getAttr('posY_screaming');
                        rotation = asset.getAttr('rotation_screaming');
                        speed = asset.getAttr('screaming_position_speed');
                        pacing = asset.getAttr('screaming_position_pacing');
                        break;
                    case 1:
                        move = asset.getAttr('moveToTALKING');
                        sizeX = asset.getAttr('sizeX_talking');
                        sizeY = asset.getAttr('sizeY_talking');
                        posX = asset.getAttr('posX_talking');
                        posY = asset.getAttr('posY_talking');
                        rotation = asset.getAttr('rotation_talking');
                        speed = asset.getAttr('talking_position_speed');
                        pacing = asset.getAttr('talking_position_pacing');
                        break;
                    default:
                        move = asset.getAttr('moveToIDLE');
                        sizeX = asset.getAttr('sizeX');
                        sizeY = asset.getAttr('sizeY');
                        posX = asset.getAttr('posX');
                        posY = asset.getAttr('posY');
                        rotation = asset.getAttr('rotationIDLE');
                        speed = asset.getAttr('idle_position_speed');
                        pacing = asset.getAttr('idle_position_pacing');
                }
                if (move == 1) {
                    new Konva.Tween({
                        node: asset,
                        duration: speed,
                        easing: Konva.Easings[pacing],
                        x: window.innerWidth / 2 + posX,
                        y: window.innerHeight / 2 + posY,
                        width: sizeX,
                        height: sizeY,
                        rotation: rotation
                    }).play();
                }
            }
        });
    }


    let animations_assets = [];
    if(imageAddedWrapper.length > 0) {
        imageAddedWrapper.forEach(function(image) {
            switch(status) {
                case 2:
                    animation = image.getAttr('animation_name_screaming')
                    speed = image.getAttr('animation_speed_screaming')
                    direction = image.getAttr('animation_direction_screaming')
                    easing = image.getAttr('animation_pacing_screaming')
                    iteration = image.getAttr('animation_iteration_screaming')
                    break;
                case 1:
                    animation = image.getAttr('animation_name_talking')
                    speed = image.getAttr('animation_speed_talking')
                    direction = image.getAttr('animation_direction_talking')
                    easing = image.getAttr('animation_pacing_talking')
                    iteration = image.getAttr('animation_iteration_talking')
                    break;
                default:
                    animation = image.getAttr('animation_name_idle')
                    speed = image.getAttr('animation_speed_idle')
                    direction = image.getAttr('animation_direction_idle')
                    easing = image.getAttr('animation_pacing_idle')
                    iteration = image.getAttr('animation_iteration_idle')
            }
            let iterationCount = (iteration === 0) ? "infinite" : iteration;

            let anim = applyAnimation(animation, image, {
                speed: speed,
                iteration: iterationCount,
                direction: direction,
                center_x: window.innerWidth / 2,
                center_y: window.innerHeight / 2,
                easing: Konva.Easings[easing]
            });
        });
    }
}

async function cursorPosition(X, Y, forced) {
    const cursorDivs = stage.find('.cursor_div');

    if (cursorDivs.length > 0) {
        cursorDivs.forEach(function(cursorDiv) {
            // Use a Konva.Tween for smooth transitions
            if (forced == cursorDiv.getAttr("forced_mouse_tracking")){
                const tween = new Konva.Tween({
                    node: cursorDiv,
                    duration: 0.1,
                    easing: Konva.Easings.Linear,
                    x: window.innerWidth / 2 + calculateX(cursorDiv, X),
                    y: window.innerHeight / 2 + calculateY(cursorDiv, Y) *-1
                });

                tween.play();
            }
        });
    }
}

function calculateX(cursorDiv, X) {
    const trackMouseX = cursorDiv.getAttr('track_mouse_x') == 1;
    const invertMouseX = cursorDiv.getAttr('invert_mouse_x') == 1;
    const cursorScaleX = cursorDiv.getAttr('cursorScaleX');

    if (trackMouseX) {
        return (invertMouseX ? -1 : 1) * X * cursorScaleX;
    }
    return 0;
}

function calculateY(cursorDiv, Y) {
    const trackMouseY = cursorDiv.getAttr('track_mouse_y') == 1;
    const invertMouseY = cursorDiv.getAttr('invert_mouse_y') == 1;
    const cursorScaleY = cursorDiv.getAttr('cursorScaleY');

    if (trackMouseY) {
        return (invertMouseY ? -1 : 1) * Y * cursorScaleY * -2;
    }
    return 0;
}

async function pool(){
    // Wheel / stick control X
    var controllerWheels = stage.find('.controller_wheelX');
    if (controllerWheels.length > 0) {
        controllerWheels.forEach(function (controllerWheel) {
            let player = controllerWheel.attrs.player;
            let invertAxis = controllerWheel.attrs.invertAxis == 0 ? 0 : 1;
            let deadzone = controllerWheel.attrs.deadzone;
            let deg = controllerWheel.attrs.deg;

            let rawx = navigator.getGamepads()[player].axes[invertAxis];
            let x = 0;
            if (rawx > deadzone) {
                x = (rawx - deadzone) / (1 - deadzone);
            } else if (rawx < -deadzone) {
                x = (rawx + deadzone) / (1 - deadzone);
            }
            let rotation = x * deg;

            controllerWheel.rotation(rotation);
        });
    }

    // Wheel / stick control Y
    var controllerWheelsY = stage.find('.controller_wheelY');
    if (controllerWheelsY.length > 0) {
        controllerWheelsY.forEach(function (controllerWheelY) {
            let player = controllerWheelY.attrs.player;
            let invertAxis = controllerWheelY.attrs.invertAxis == 0 ? 1 : 0;
            let deadzone = controllerWheelY.attrs.deadzone;
            let deg = controllerWheelY.attrs.deg;

            let rawy = navigator.getGamepads()[player].axes[invertAxis];
            let x = 0;
            if (rawy > deadzone) {
                x = (rawy - deadzone) / (1 - deadzone);
            } else if (rawy < -deadzone) {
                x = (rawy + deadzone) / (1 - deadzone);
            }
            let rotation = x * deg;

            controllerWheelY.scale({ x: 1, y: 1 + ((-Math.abs(rotation)) / 100) });
            if (rotation > 0) {
                controllerWheelY.y(controllerWheelY.attrs.offsetY_var + rotation * 2);
            } else {
                controllerWheelY.y(controllerWheelY.attrs.offsetY_var + rotation * 3);
            }
        });
    }

    // Whammy / stick control X
    var controllerWhammyWheels = stage.find('.Whammywheel');
    if (controllerWhammyWheels.length > 0) {
        controllerWhammyWheels.forEach(function (controllerWhammyWheel) {
            let player = controllerWhammyWheel.attrs.player;
            let invertAxis = controllerWhammyWheel.attrs.invertAxis == 0 ? 2 : 3;
            let deadzone = controllerWhammyWheel.attrs.deadzone;
            let deg = controllerWhammyWheel.attrs.deg;

            let rawx = navigator.getGamepads()[player].axes[invertAxis];
            let x = 0;
            if (rawx > deadzone) {
                x = (rawx - deadzone) / (1 - deadzone);
            } else if (rawx < -deadzone) {
                x = (rawx + deadzone) / (1 - deadzone);
            }
            let rotation = x * deg;

            controllerWhammyWheel.rotation(rotation);
        });
    }

    // Wheel / stick 2 control X and Y
    var controllerWheelsZ = stage.find('.controller_wheelZ');
    if (controllerWheelsZ.length > 0) {
        controllerWheelsZ.forEach(function (controllerWheelZ) {
            let player = controllerWheelZ.attrs.player;
            let deadzone = controllerWheelZ.attrs.deadzone;
            let deg = controllerWheelZ.attrs.deg;

            let rawx = navigator.getGamepads()[player].axes[2];
            let x = 0;
            if (rawx > deadzone) {
                x = (rawx - deadzone) / (1 - deadzone);
            } else if (rawx < -deadzone) {
                x = (rawx + deadzone) / (1 - deadzone);
            }
            let rotationx = x * deg;

            let rawy = navigator.getGamepads()[player].axes[3];
            let y = 0;
            if (rawy > deadzone) {
                y = (rawy - deadzone) / (1 - deadzone);
            } else if (rawy < -deadzone) {
                y = (rawy + deadzone) / (1 - deadzone);
            }
            let rotationy = y * deg;

            controllerWheelZ.scale({ x: 1 + ((-Math.abs(rotationx)) / 100 / 2), y: 1 + ((-Math.abs(rotationy)) / 100 / 2) });

            controllerWheelZ.x(controllerWheelZ.attrs.offsetX_var - rotationx * 3);
            if (rotationy > 0) {
                controllerWheelZ.y(controllerWheelZ.attrs.offsetY_var - rotationy / 1.5);
            } else {
                controllerWheelZ.y(controllerWheelZ.attrs.offsetY_var - rotationy * 3);
            }
        });
    }

    // Button control
    var controllerButtons = stage.find('.controller_buttons');
    if (controllerButtons.length > 0) {
        controllerButtons.forEach(function (controllerButton) {
            let player = controllerButton.attrs.player;
            let buttons = navigator.getGamepads()[player].buttons;
            let left = false;
            let right = false;

            for (let i = 0; i < buttons.length; i++) {
                if (buttons[i].pressed) {
                    if (!left && leftButtons.indexOf(i) !== -1) {
                        left = true;
                    } else if (!right && rightButtons.indexOf(i) !== -1) {
                        right = true;
                    }
                }
            }

            let mode = controllerButton.attrs.mode;
            let buttonsAttr = controllerButton.attrs.buttons;
            let posLeftX = controllerButton.attrs.posLeftX;
            let posLeftY = controllerButton.attrs.posLeftY;
            let rotationLeft = controllerButton.attrs.rotationLeft;
            let posRightX = controllerButton.attrs.posRightX;
            let posRightY = controllerButton.attrs.posRightY;
            let rotationRight = controllerButton.attrs.rotationRight;
            let posBothX = controllerButton.attrs.posBothX;
            let posBothY = controllerButton.attrs.posBothY;
            let rotationBoth = controllerButton.attrs.rotationBoth;

            let x = controllerButton.attrs.offsetX_var
            let y = controllerButton.attrs.offsetY_var

            switch (true) {
                case left && right:
                    if (mode == "display") {
                        if (buttonsAttr == 3) {
                            controllerButton.show();
                        } else {
                            controllerButton.hide();
                        }
                    } else {
                        controllerButton.to({
                            x: x + posBothX,
                            y: y + posBothY,
                            rotation: rotationBoth,
                            duration: 0.1,
                        });
                    }
                    break;
                case left:
                    if (mode == "display") {
                        if (buttonsAttr == 1) {
                            controllerButton.show();
                        } else {
                            controllerButton.hide();
                        }
                    } else {
                        controllerButton.to({
                            x: x + posLeftX,
                            y: y + posLeftY,
                            rotation: rotationLeft,
                            duration: 0.1,
                        });
                    }
                    break;
                case right:
                    if (mode == "display") {
                        if (buttonsAttr == 2) {
                            controllerButton.show();
                        } else {
                            controllerButton.hide();
                        }
                    } else {
                        controllerButton.to({
                            x: x + posRightX,
                            y: y + posRightY,
                            rotation: rotationRight,
                            duration: 0.1,
                        });
                    }
                    break;
                default:
                    if (mode == "display") {
                        if (buttonsAttr == 0) {
                            controllerButton.show();
                        } else {
                            controllerButton.hide();
                        }
                    } else {
                        controllerButton.to({
                            x: x + 0,
                            y: y + 0,
                            rotation: 0,
                            duration: 0.1,
                        });
                    }
                    break;
            }
        });
    }

    // Guitar control
    var guitarButtons = stage.find('.guitar_buttons');
    if (guitarButtons.length > 0) {
        guitarButtons.forEach(function (guitarButton) {
            let player = guitarButton.attrs.player;
            let buttons = navigator.getGamepads()[player].buttons;

            let up = false;
            let down = false;

            let green = false;
            let red = false;
            let yellow = false;
            let blue = false;
            let orange = false;

            let rawx = navigator.getGamepads()[player].axes[9];

            if (!up && parseInt(rawx) == -1) {
                up = true;
            } else if (!down && parseInt(rawx) == 0) {
                down = true;
            }

            for (let i = 0; i < buttons.length; i++) {
                if (buttons[i].pressed) {
                    if (!green && i == 1) {
                        green = true;
                    } else if (!red && i == 2) {
                        red = true;
                    } else if (!yellow && i == 0) {
                        yellow = true;
                    } else if (!blue && i == 3) {
                        blue = true;
                    } else if (!orange && i == 4) {
                        orange = true;
                    }
                }
            }

            let posGuitarUpX = guitarButton.attrs.offsetX_var + guitarButton.attrs.posGuitarUpX;
            let posGuitarUpY = guitarButton.attrs.offsetY_var + guitarButton.attrs.posGuitarUpY;
            let rotationGuitarUp = guitarButton.attrs.rotationGuitarUp;
            let posGuitarDownX = guitarButton.attrs.offsetX_var + guitarButton.attrs.posGuitarDownX;
            let posGuitarDownY = guitarButton.attrs.offsetY_var + guitarButton.attrs.posGuitarDownY;
            let rotationGuitarDown = guitarButton.attrs.rotationGuitarDown;

            switch (true) {
                case up:
                    guitarButton.x(posGuitarUpX);
                    guitarButton.y(posGuitarUpY);
                    guitarButton.rotation(rotationGuitarUp);
                    break;
                case down:
                    guitarButton.x(posGuitarDownX);
                    guitarButton.y(posGuitarDownY);
                    guitarButton.rotation(rotationGuitarDown);
                    break;
                default:
                    guitarButton.x(guitarButton.attrs.offsetX_var + 0);
                    guitarButton.y(guitarButton.attrs.offsetY_var + 0);
                    guitarButton.rotation(0);
                    break;
            }

            let chordsString = guitarButton.attrs.chords;

            if (chordsString) {
                let colorsList = chordsString.split(',').map(color => color.trim());

                if (colorsList.includes("None")) {
                    if (green || red || yellow || blue || orange) {
                        guitarButton.hide();
                    } else {
                        guitarButton.show();
                    }
                } else {
                    let allColorsTrue = colorsList.every(color => {
                        let variableName = color.toLowerCase();
                        return eval(variableName);
                    });

                    if (allColorsTrue) {
                        guitarButton.show();
                    } else {
                        guitarButton.hide();
                    }
                }
            }
        });
    }

    window.requestAnimationFrame(pool);
    // }
}

function animateBlinkOpen(group) {
    return new Konva.Animation(function(frame) {
        var opacity = (frame.time % 3000) < 250 ? 0 : 1;
        group.opacity(opacity);
    }, group.getLayer());
}

function animateBlinkClosed(group) {
    return new Konva.Animation(function(frame) {
        var opacity = (frame.time % 3000) < 250 ? 1 : 0;
        group.opacity(opacity);
    }, group.getLayer());
}

function animateShadowColor(image) {
    var colors = ['black','white'];
    var currentIndex = 0;
    var lastColorChangeTime = 0;
    var interval = 200;

    return new Konva.Animation(function(frame) {
        // Calculate time elapsed since the last color change
        var elapsedTime = frame.time - lastColorChangeTime;

        // Check if enough time has passed to change color
        if (elapsedTime > interval) {
            var currentColor = colors[currentIndex % colors.length];
            image.shadowColor(currentColor);
            currentIndex = (currentIndex + 1) % colors.length;
            lastColorChangeTime = frame.time;
        }
    }, image.getLayer());
}

function startAnimations() {
    var blinkingOpenGroups = stage.find('.blinking_open');
    var blinkingClosedGroups = stage.find('.blinking_closed');
    var being_editedImages = stage.find('.being_edited');

    blinkingOpenGroups.forEach(function(group) {
        animateBlinkOpen(group).start();
    });

    blinkingClosedGroups.forEach(function(group) {
        animateBlinkClosed(group).start();
    });

    being_editedImages.forEach(function(image) {
        animateShadowColor(image).start();
    });
}

function destroy_animations() {
    const imageWrapper = stage.find('.idle_animation');
    const imageAddedWrapper = stage.find('.added_animation');

    if (imageWrapper.length > 0) {
        imageWrapper.forEach(function(image, index) {
            let anim = applyAnimation("None", image, {
                speed: 6.0,
                iteration: "infinite",
                direction: "normal",
                center_x: window.innerWidth / 2,
                center_y: window.innerHeight / 2,
                easing: Konva.Easings["Linear"]
            }, True);
        });
    }

    let animations_assets = [];
    if(imageAddedWrapper.length > 0) {
        imageAddedWrapper.forEach(function(image) {

            let anim = applyAnimation("None", image, {
                speed: 6.0,
                iteration: "infinite",
                direction: "normal",
                center_x: window.innerWidth / 2,
                center_y: window.innerHeight / 2,
                easing: Konva.Easings["linear"]
            }, True);
        });
    }
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
                opacity: "talking_closed" in talking ? 1 : 0

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

            gifler(imageData.route).frames(imageObj, (ctx, frame) => {
                imageObj.width = frame.width;
                imageObj.height = frame.height;
                ctx.drawImage(frame.buffer, 0, 0);
                layer.draw();
            });
        } else {
            // Handle regular images
            var imageObj = new Image();
            imageObj.src = imageData.route;
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

        //konvaImage.on('mouseenter', function () {
        //    stage.container().style.cursor = 'move';
        //});

        //konvaImage.on('mouseleave', function () {
        //    stage.container().style.cursor = 'default';
        //});

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